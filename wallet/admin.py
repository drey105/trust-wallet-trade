from django.contrib import admin
from django.db import transaction
from django.db.models import F
from .models import Wallet, Transaction, AdminDeposit


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "deposit_address", "updated_at")
    search_fields = ("user__username", "deposit_address")
    readonly_fields = ("balance", "created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("user", "balance", "created_at", "updated_at")
        return ("balance", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__user__username",)
    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                old_obj = Transaction.objects.get(pk=obj.pk)
                if old_obj.transaction_type == Transaction.DEPOSIT:
                    old_obj.wallet.balance = F("balance") - old_obj.amount
                else:
                    old_obj.wallet.balance = F("balance") + old_obj.amount
                old_obj.wallet.save(update_fields=["balance"])

                if obj.transaction_type == Transaction.DEPOSIT:
                    obj.wallet.balance = F("balance") + obj.amount
                else:
                    obj.wallet.balance = F("balance") - obj.amount
                obj.wallet.save(update_fields=["balance"])
            else:
                if obj.transaction_type == Transaction.DEPOSIT:
                    obj.wallet.balance = F("balance") + obj.amount
                else:
                    obj.wallet.balance = F("balance") - obj.amount
                obj.wallet.save(update_fields=["balance"])
            super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        with transaction.atomic():
            if obj.transaction_type == Transaction.DEPOSIT:
                obj.wallet.balance = F("balance") - obj.amount
            else:
                obj.wallet.balance = F("balance") + obj.amount
            obj.wallet.save(update_fields=["balance"])
            super().delete_model(request, obj)


@admin.register(AdminDeposit)
class AdminDepositAdmin(admin.ModelAdmin):
    list_display = ("user", "admin", "transaction_type", "amount", "created_at")
    list_filter = ("admin", "transaction_type", "created_at")
    search_fields = ("user__username", "admin__username")
    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.admin = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("user", "admin", "amount", "created_at")
        return ("created_at",)

    def has_delete_permission(self, request, obj=None):
        return False
