from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomLoginView, CurrentUserView, UserListView

urlpatterns = [
    # Authentication routes
    path('login/', CustomLoginView.as_view(), name='auth_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile routes
    path('me/', CurrentUserView.as_view(), name='auth_me'),

    # User management routes (Admin only)
    path('users/', UserListView.as_view(), name='user_list'),
]