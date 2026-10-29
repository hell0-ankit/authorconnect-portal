import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def _env_list(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value.")


DEBUG = False

RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS and RENDER_HOSTNAME:
    ALLOWED_HOSTS = [RENDER_HOSTNAME]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Set ALLOWED_HOSTS or RENDER_EXTERNAL_HOSTNAME for production."
    )

CSRF_TRUSTED_ORIGINS = _env_list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS")
if RENDER_HOSTNAME:
    render_origin = f"https://{RENDER_HOSTNAME}"
    if not CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = [render_origin]
    if not CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS = [render_origin]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", False
)
SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DB_CONN_MAX_AGE", "60"))
