from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    deposit_address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"

    def __str__(self):
        return f"{self.user.username} wallet"

    def get_deposit_address(self):
        return self.deposit_address or settings.FIXED_WALLET_ADDRESS

    def deposit(self, amount, note=""):
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            wallet.balance = F("balance") + amount
            wallet.save(update_fields=["balance"])
            wallet.refresh_from_db()
            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type=Transaction.DEPOSIT,
                note=note,
            )
            return wallet

    def withdraw(self, amount, note=""):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            if wallet.balance < amount:
                raise ValueError("Insufficient funds for this withdrawal.")
            wallet.balance = F("balance") - amount
            wallet.save(update_fields=["balance"])
            wallet.refresh_from_db()
            Transaction.objects.create(wallet=wallet, amount=amount, transaction_type=Transaction.WITHDRAWAL, note=note)
            return wallet


class Transaction(models.Model):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSACTION_TYPE_CHOICES = [
        (DEPOSIT, "Deposit"),
        (WITHDRAWAL, "Withdrawal"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=12, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount}"


class AdminDeposit(models.Model):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSACTION_TYPE_CHOICES = [
        (DEPOSIT, "Deposit"),
        (WITHDRAWAL, "Withdrawal"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_deposits",
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_actions",
    )
    transaction_type = models.CharField(
        max_length=12,
        choices=TRANSACTION_TYPE_CHOICES,
        default=DEPOSIT,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Admin Deposit"
        verbose_name_plural = "Admin Deposits"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Admin {self.get_transaction_type_display()} of {self.amount} to {self.user.username}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        with transaction.atomic():
            if is_new:
                wallet, _ = Wallet.objects.get_or_create(user=self.user)
                if self.transaction_type == self.DEPOSIT:
                    wallet.deposit(self.amount, note=self.note or f"Admin deposit to {self.user.username}")
                else:
                    wallet.withdraw(self.amount)
            super().save(*args, **kwargs)
