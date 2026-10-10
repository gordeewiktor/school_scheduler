import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from config.env import EnvironmentConfigurationError, parse_bool, parse_int, parse_list, required

BASE_DIR = Path(__file__).resolve().parent.parent

# Local-dev convenience only: populates os.environ from a gitignored
# .env file if one exists. A real deployment sets these directly in
# its own environment instead; load_dotenv() silently does nothing if
# .env is absent, so this is a no-op there. load_dotenv() never
# overrides a variable that's already set in the environment, so an
# explicitly-exported value (e.g. in a deployment platform, or in a
# test harness) always wins over whatever is in .env.
load_dotenv(BASE_DIR / ".env")


def _required_env(name: str, *, hint: str = "") -> str:
    try:
        return required(name, hint=hint)
    except EnvironmentConfigurationError as exc:
        raise ImproperlyConfigured(str(exc)) from exc


# DJANGO_ENV is the one explicit switch between development and
# production defaults (see README.md's "Production configuration"
# section). Everything else is still individually overridable via its
# own environment variable — this only changes what each setting
# defaults to when its own variable is absent.
DJANGO_ENV = os.environ.get("DJANGO_ENV", "development").strip().lower()
if DJANGO_ENV not in ("development", "production"):
    raise ImproperlyConfigured(
        f"DJANGO_ENV must be 'development' or 'production', got {DJANGO_ENV!r}."
    )
IS_PRODUCTION = DJANGO_ENV == "production"

if IS_PRODUCTION:
    # Never fall back to a development secret key in production — if
    # SECRET_KEY isn't set, fail loudly instead of running insecurely.
    SECRET_KEY = _required_env(
        "SECRET_KEY",
        hint="Generate one with `python -c \"from django.core.management.utils "
        "import get_random_secret_key; print(get_random_secret_key())\"` and set "
        "it directly in the production environment — never commit it.",
    )
else:
    # Convenience default so a fresh checkout works without first
    # generating a key. Clearly marked as insecure (matches Django's
    # own "django-insecure-" convention for generated dev keys) and
    # only ever used when DJANGO_ENV is not "production".
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "django-insecure-local-development-only-key"
    )

try:
    DEBUG = parse_bool("DEBUG", default=not IS_PRODUCTION)
except EnvironmentConfigurationError as exc:
    raise ImproperlyConfigured(str(exc)) from exc

# Belt-and-suspenders: even if someone explicitly sets DEBUG=true in a
# production environment, refuse to start rather than honor it.
# DEBUG=True in production would show full tracebacks, local variable
# values, and settings to any visitor on an unhandled exception.
if IS_PRODUCTION and DEBUG:
    raise ImproperlyConfigured(
        "DEBUG must not be True when DJANGO_ENV=production. Remove DEBUG "
        "from the environment, or set it to false."
    )

if IS_PRODUCTION:
    ALLOWED_HOSTS = parse_list("ALLOWED_HOSTS")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be set (comma-separated) when DJANGO_ENV=production."
        )
else:
    ALLOWED_HOSTS = parse_list("ALLOWED_HOSTS", default="localhost,127.0.0.1")

# Not required anywhere: same-origin, non-proxied setups work without
# it. Only needed once a real domain is deployed behind HTTPS/a proxy,
# or across subdomains — set it then, via the environment. No
# invented placeholder domain is hardcoded here.
CSRF_TRUSTED_ORIGINS = parse_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "app" / "presentation" / "web" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "app.presentation.web.school_access.school_context",
                "app.presentation.web.navigation.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# PostgreSQL is the project's standard database backend, for local
# development, testing, and production alike — there is no SQLite
# fallback. Connection settings always come from the environment, never
# hardcoded, so the same settings.py works unchanged in every
# environment; only the environment variables differ. pytest-django
# runs tests against a separate, automatically created/destroyed
# "test_<DB_NAME>" database on this same connection, never DB_NAME
# itself.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _required_env(
            "DB_NAME", hint="Copy .env.example to .env and fill in your PostgreSQL credentials."
        ),
        "USER": _required_env(
            "DB_USER", hint="Copy .env.example to .env and fill in your PostgreSQL credentials."
        ),
        "PASSWORD": _required_env(
            "DB_PASSWORD", hint="Copy .env.example to .env and fill in your PostgreSQL credentials."
        ),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
# Where `collectstatic` gathers files (this app's own pages have none
# of their own — only Django Admin's built-in CSS/JS need collecting).
# Collecting them here does not serve them: a production deployment
# still needs a web server or a static-file-serving solution (e.g.
# nginx, or a package like whitenoise) pointed at this directory —
# `collectstatic` alone does not make it reachable over HTTP.
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "schedule"
LOGOUT_REDIRECT_URL = "login"

# --- Production security settings ---------------------------------
#
# Each setting below defaults to Django's safe-for-production value
# only when DJANGO_ENV=production, and to a value that keeps local
# `runserver` over plain http:// working otherwise. Every one is still
# individually overridable via its own environment variable.
#
# Must be configured before a real deployment (see README.md):
#   - DJANGO_ENV=production
#   - SECRET_KEY (required, no fallback — see above)
#   - ALLOWED_HOSTS (required — see above)
#   - CSRF_TRUSTED_ORIGINS, once a domain is chosen (see above)
#   - BEHIND_TLS_PROXY=true, but ONLY if actually deployed behind a
#     reverse proxy/load balancer that terminates TLS and sets
#     X-Forwarded-Proto (see below) — enabling it otherwise lets a
#     client spoof that header and defeat SECURE_SSL_REDIRECT.

try:
    SECURE_SSL_REDIRECT = parse_bool("SECURE_SSL_REDIRECT", default=IS_PRODUCTION)
    SESSION_COOKIE_SECURE = parse_bool("SESSION_COOKIE_SECURE", default=IS_PRODUCTION)
    CSRF_COOKIE_SECURE = parse_bool("CSRF_COOKIE_SECURE", default=IS_PRODUCTION)
    BEHIND_TLS_PROXY = parse_bool("BEHIND_TLS_PROXY", default=False)
except EnvironmentConfigurationError as exc:
    raise ImproperlyConfigured(str(exc)) from exc

if BEHIND_TLS_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS is configured conservatively and opt-in via its default: 0
# (disabled) unless DJANGO_ENV=production, and even then a short 1
# hour rather than the eventual 1-year recommendation — HSTS tells
# browsers to refuse plain http:// for this long, which is awkward to
# undo if something is misconfigured. Raise SECURE_HSTS_SECONDS
# gradually (e.g. to 86400, then 604800, then 31536000) only after
# confirming HTTPS works correctly site-wide. Subdomains and preload
# are never enabled by default — both are a larger, harder-to-reverse
# commitment than this project needs yet.
try:
    SECURE_HSTS_SECONDS = parse_int(
        "SECURE_HSTS_SECONDS", default=3600 if IS_PRODUCTION else 0, minimum=0
    )
except EnvironmentConfigurationError as exc:
    raise ImproperlyConfigured(str(exc)) from exc
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# --- Logging ---------------------------------------------------------
#
# Minimal and container/platform-friendly: everything goes to stderr
# via a plain StreamHandler, which is what a containerized or
# PaaS-style deployment captures as its log output — no file handling,
# no email, no third-party logging package. Unlike Django's own
# DEFAULT_LOGGING (which only logs to console when DEBUG=True), this
# always logs, so production errors are never silent. Never logs
# request bodies, so passwords/session data are never written out —
# Django's own request-exception logging (django.request) logs the
# exception and the request path/method only.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # Deliberately "INFO" even in development, not "DEBUG": Django's
        # own child loggers (e.g. django.db.backends) inherit whatever
        # level isn't otherwise set, and django.db.backends at DEBUG
        # logs the full text of every SQL query — noisy, and not what
        # "appropriate level for the environment" is meant to enable.
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "app": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
