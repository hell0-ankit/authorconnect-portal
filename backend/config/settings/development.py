from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# CORS for local Vite dev server
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Development email backend 
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'