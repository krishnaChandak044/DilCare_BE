"""
Accounts — Custom User model with email-based authentication.
Enhanced with UserSettings and UserDevice for FCM push notifications.
"""
import string
import random
import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class UserSettings(models.Model):
    """User preferences and settings."""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('gu', 'Gujarati'),
        ('mr', 'Marathi'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('ml', 'Malayalam'),
        ('pa', 'Punjabi'),
    ]
    UNIT_CHOICES = [
        ('metric', 'Metric'),
        ('imperial', 'Imperial'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    notifications_enabled = models.BooleanField(default=True)
    medicine_reminders = models.BooleanField(default=True)
    appointment_reminders = models.BooleanField(default=True)
    health_tips_enabled = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    units = models.CharField(max_length=10, choices=UNIT_CHOICES, default='metric')
    daily_step_goal = models.IntegerField(default=10000)
    daily_water_goal = models.IntegerField(default=8)  # glasses
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_settings"
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"

    def __str__(self):
        return f"Settings for {self.user.email}"


class UserDevice(models.Model):
    """Store FCM tokens for push notifications."""
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_token = models.CharField(max_length=500)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    device_name = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_devices"
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        unique_together = ['user', 'device_token']

    def __str__(self):
        return f"{self.user.email} - {self.device_type}"


# Signal to create UserSettings when a new User is created
@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Automatically create UserSettings when a User is created."""
    if created:
        UserSettings.objects.create(user=instance)
