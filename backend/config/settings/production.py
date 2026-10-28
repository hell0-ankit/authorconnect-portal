import os

from .base import *  # noqa: F403


def _required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} must be set when using production settings")
    return value


def _env_list(name):
    return [
        item.strip()
        for item in os.getenv(name, "").split(",")
        if item.strip()
    ]


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
        raise ValueError(f"{name} must be true or false")
    return value.lower() in {"true", "1", "yes"}


DEBUG = False

# Production deployments must provide explicit origins and hosts.
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _env_list("CSRF_TRUSTED_ORIGINS")

if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must contain at least one hostname")
if not CORS_ALLOWED_ORIGINS:
    raise ValueError("CORS_ALLOWED_ORIGINS must contain at least one origin")
if not CSRF_TRUSTED_ORIGINS:
    raise ValueError("CSRF_TRUSTED_ORIGINS must contain at least one origin")

required_database_settings = (
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
)
for setting_name in required_database_settings:
    _required_env(setting_name)

# HTTPS and proxy configuration.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", True
)
SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", True)
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")

# Keep database connections alive according to the deployment policy.
DATABASES["default"]["CONN_MAX_AGE"] = int(
    os.getenv("DB_CONN_MAX_AGE", "60")
)
