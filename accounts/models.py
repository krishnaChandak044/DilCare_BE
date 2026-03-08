"""
Accounts — Custom User model with email-based authentication.
"""
import string
import random

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


def generate_link_code(length=6):
    """Generate a random 6-character alphanumeric link code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


class UserManager(BaseUserManager):
    """Custom manager that uses email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User — email is the primary identifier.
    Stores profile fields needed by the frontend ProfileScreen.
    """
    username = None  # remove username field
    email = models.EmailField(unique=True)

    # ── Profile fields (matching frontend ProfileScreen) ──────────
    phone = models.CharField(max_length=20, blank=True, default="")
    age = models.CharField(max_length=5, blank=True, default="")
    address = models.TextField(blank=True, default="")
    emergency_contact = models.CharField(max_length=20, blank=True, default="")
    blood_group = models.CharField(max_length=5, blank=True, default="")

    # ── Family linking ────────────────────────────────────────────
    parent_link_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_link_code,
        help_text="Unique 6-char code for family linking",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are handled by create_user

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def regenerate_link_code(self):
        """Generate a new unique link code and save."""
        while True:
            new_code = generate_link_code()
            if not User.objects.filter(parent_link_code=new_code).exists():
                self.parent_link_code = new_code
                self.save(update_fields=["parent_link_code"])
                return new_code
