from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_for_token(raw_token):
    try:
        token = AccessToken(raw_token)
        user_id = token[api_settings.USER_ID_CLAIM]
        user = User._default_manager.get(
            **{api_settings.USER_ID_FIELD: user_id}
        )
    except (TokenError, KeyError, User.DoesNotExist, TypeError, ValueError):
        return AnonymousUser()
    if not getattr(user, 'is_active', False):
        return AnonymousUser()
    return user
