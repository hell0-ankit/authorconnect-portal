from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        AUTHOR = 'AUTHOR', 'Author'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AUTHOR,
        help_text="Role-based access control for portal access"
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_author_user(self):
        return self.role == self.Role.AUTHOR

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"