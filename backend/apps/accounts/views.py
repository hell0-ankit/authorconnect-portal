from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import CustomTokenObtainPairSerializer, UserSerializer
from apps.core.permissions import IsAdminUserRole

User = get_user_model()


class CustomLoginView(TokenObtainPairView):
    """
    Public endpoint: Authenticates user credentials and returns JWT access/refresh tokens with role details.
    """
    serializer_class = CustomTokenObtainPairSerializer


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Protected endpoint: Retrieve or update currently authenticated user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """
    Admin-only endpoint: List users with optional role filtering (e.g. ?role=AUTHOR or ?role=ADMIN).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        queryset = User.objects.all().order_by('username')
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role.upper())
        return queryset