# Trust Wallet Django MVP

A complete wallet application built with Django.

## Features
- User registration and login
- Secure wallet dashboard with balance
- Deposit and withdrawal operations
- Transaction history
- Atomic updates and balance validation
- REST API endpoints for wallet and transaction access
- Environment-based configuration

## Setup

```bash
cd /Users/dareydigitals/Documents/python/trust-wallet-trade
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
cp .env.example .env
# edit .env if needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Local URLs
- http://127.0.0.1:8000/ - Dashboard / login / register
- http://127.0.0.1:8000/admin/ - Django admin
- API endpoints:
  - `/api/wallet/`
  - `/api/transactions/`
  - `/api/deposit/`
  - `/api/withdraw/`

## Notes
- Defaults to SQLite for development.
- Use PostgreSQL in production by setting `DB_ENGINE` and credentials in `.env`.
- `SECRET_KEY` should be kept secret in production.
