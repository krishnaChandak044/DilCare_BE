"""
Accounts — Custom User model with email-based authentication.
Enhanced with UserSettings and UserDevice for FCM push notifications.
"""
import string
import random
import uuid
from datetime import datetime

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


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
    gender = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="male, female, other, or prefer_not_say",
    )

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


class Notification(models.Model):
    """Store notification history for analytics and notification center."""
    NOTIFICATION_TYPES = [
        ('sos_alert', 'SOS Alert'),
        ('medication_reminder', 'Medication Reminder'),
        ('health_update', 'Health Update'),
        ('family_message', 'Family Message'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('activity_goal', 'Activity Goal'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    action = models.CharField(max_length=100, blank=True, default="")
    data = models.JSONField(default=dict, blank=True)
    
    # Tracking
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])

    def mark_as_opened(self):
        """Mark notification as opened/clicked."""
        if not self.opened:
            self.opened = True
            self.opened_at = timezone.now()
            self.save(update_fields=['opened', 'opened_at'])


class NotificationPreference(models.Model):
    """User notification preferences and quiet hours."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Notification categories
    sos_alerts = models.BooleanField(default=True)
    medication_reminders = models.BooleanField(default=True)
    health_updates = models.BooleanField(default=True)
    family_messages = models.BooleanField(default=True)
    appointment_reminders = models.BooleanField(default=True)
    activity_goals = models.BooleanField(default=True)
    
    # Sound & vibration
    notification_sound = models.BooleanField(default=True)
    notification_vibration = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default="22:00", help_text="HH:MM format")
    quiet_hours_end = models.TimeField(default="08:00", help_text="HH:MM format")
    
    # Except for emergencies (SOS, critical health alerts)
    quiet_hours_exception_emergency = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification preferences for {self.user.email}"

    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled:
            return False
        
        from datetime import datetime
        now = datetime.now().time()
        
        # Handle case where quiet hours cross midnight (e.g., 22:00 to 08:00)
        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= now < self.quiet_hours_end
        else:
            return now >= self.quiet_hours_start or now < self.quiet_hours_end

    def should_send_notification(self, notification_type):
        """Determine if notification should be sent based on preferences."""
        # Check if we're in quiet hours
        if self.is_in_quiet_hours():
            # Allow emergency notifications even during quiet hours
            if notification_type == 'sos_alert' and self.quiet_hours_exception_emergency:
                return True
            return False
        
        # Check specific notification type preference
        preference_map = {
            'sos_alert': self.sos_alerts,
            'medication_reminder': self.medication_reminders,
            'health_update': self.health_updates,
            'family_message': self.family_messages,
            'appointment_reminder': self.appointment_reminders,
            'activity_goal': self.activity_goals,
        }
        
        return preference_map.get(notification_type, True)


# Signal to create UserSettings and NotificationPreference when a new User is created
@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Automatically create UserSettings and NotificationPreference when a User is created."""
    if created:
        UserSettings.objects.get_or_create(user=instance)
        NotificationPreference.objects.get_or_create(user=instance)
