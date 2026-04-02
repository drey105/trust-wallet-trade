from django.urls import path
from . import views

app_name = "wallet"

urlpatterns = [
    path("", views.WalletDashboardView.as_view(), name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("deposit/", views.DepositView.as_view(), name="deposit"),
    path("withdraw/", views.WithdrawView.as_view(), name="withdraw"),
    path("transactions/", views.TransactionHistoryView.as_view(), name="transactions"),
    path("api/wallet/", views.wallet_api, name="api-wallet"),
    path("api/transactions/", views.transactions_api, name="api-transactions"),
    path("api/deposit/", views.deposit_api, name="api-deposit"),
    path("api/withdraw/", views.withdraw_api, name="api-withdraw"),
]
