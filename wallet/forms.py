from decimal import Decimal
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "input-field"}))

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class TransactionForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"class": "input-field", "placeholder": "Amount"}),
    )


class AdminDepositForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="User",
        required=False,
        empty_label="All users",
        widget=forms.Select(attrs={"class": "input-field"}),
    )
    transaction_type = forms.ChoiceField(
        choices=[
            ("deposit", "Deposit"),
            ("withdrawal", "Withdraw"),
        ],
        label="Action",
        widget=forms.Select(attrs={"class": "input-field"}),
        initial="deposit",
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"class": "input-field", "placeholder": "Amount"}),
    )
