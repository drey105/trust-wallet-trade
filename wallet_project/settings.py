import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env when available
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def get_env_variable(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"The {name} environment variable is required.")
    return value

SECRET_KEY = get_env_variable("SECRET_KEY", "change-me-locally", required=True)
DEBUG = get_env_variable("DEBUG", "False") == "True"
ALLOWED_HOSTS = get_env_variable("ALLOWED_HOSTS", "yourdomain.com www.yourdomain.com").split()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "wallet",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wallet_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "wallet" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wallet_project.wsgi.application"

DB_ENGINE = get_env_variable("DB_ENGINE", "django.db.backends.sqlite3")
if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": get_env_variable("DB_NAME", required=True),
            "USER": get_env_variable("DB_USER", required=True),
            "PASSWORD": get_env_variable("DB_PASSWORD", required=True),
            "HOST": get_env_variable("DB_HOST", "localhost"),
            "PORT": get_env_variable("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "wallet" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

EMAIL_BACKEND = get_env_variable("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = get_env_variable("EMAIL_HOST", "localhost")
EMAIL_PORT = int(get_env_variable("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = get_env_variable("EMAIL_USE_TLS", "False") == "True"
DEFAULT_FROM_EMAIL = get_env_variable("DEFAULT_FROM_EMAIL", "webmaster@localhost")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FIXED_WALLET_ADDRESS = get_env_variable("FIXED_WALLET_ADDRESS", "0xDEADBEAF1234567890ABCDEF1234567890")

LOGIN_URL = "wallet:login"
LOGIN_REDIRECT_URL = "wallet:dashboard"
LOGOUT_REDIRECT_URL = "wallet:login"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
