import os

from .base import *  # noqa: F403


def _env_list(name):
    val = os.getenv(name, "").strip()
    return [item.strip() for item in val.split(",") if item.strip()]


def _env_bool(name, default=True):
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"true", "1", "yes"}


DEBUG = False

# Render se automatically domain uthayega, nahi mila to fallback karega
RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME", "authorconnect-portal.onrender.com")

# 1. ALLOWED_HOSTS
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS") or [RENDER_HOSTNAME, "localhost", "127.0.0.1"]

# 2. CSRF & CORS (Form submission aur login ke liye zaroori)
CSRF_TRUSTED_ORIGINS = _env_list("CSRF_TRUSTED_ORIGINS") or [f"https://{RENDER_HOSTNAME}"]
CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS") or [f"https://{RENDER_HOSTNAME}"]

# HTTPS & Proxy Settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Database connection
if "DATABASES" in locals() and "default" in DATABASES:
    DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DB_CONN_MAX_AGE", "60"))