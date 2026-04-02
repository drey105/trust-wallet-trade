import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wallet_project.settings')
import django
django.setup()
from django.contrib.auth.models import User
from wallet.models import Wallet

admin, _ = User.objects.get_or_create(username='__admin_test__', defaults={'email': 'admin@test.com', 'is_staff': True})
admin.set_password('pass')
admin.save()
user, _ = User.objects.get_or_create(username='__user_test__', defaults={'email': 'user@test.com', 'is_staff': False})
user.set_password('pass')
user.save()
wallet, created = Wallet.objects.get_or_create(user=user)
print('wallet existed', not created, 'balance', wallet.balance)
wallet.deposit(10, note='Admin deposit test')
wallet.refresh_from_db()
print('after deposit balance', wallet.balance)
print('transactions count', wallet.transactions.count())
for t in wallet.transactions.all():
    print('transaction', t.transaction_type, t.amount, repr(t.note))
