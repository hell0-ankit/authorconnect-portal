from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminUserRole(BasePermission):
    """
    Allows access only to Admin users or superusers.
    """
    message = "You do not have administrative privileges to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == User.Role.ADMIN or request.user.is_superuser)
        )


class IsAuthorUserRole(BasePermission):
    """
    Allows access only to Author users.
    """
    message = "Only registered authors can access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.AUTHOR
        )