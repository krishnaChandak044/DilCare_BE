from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import SoftDeleteModel, TimeStampedModel
from family.models import FamilyLink


class LocationShareSetting(TimeStampedModel):
    PRECISION_CHOICES = [
        ("exact", "Exact"),
        ("approximate", "Approximate"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location_share_settings",
    )
    sharing_enabled = models.BooleanField(default=True)
    share_precision = models.CharField(max_length=20, choices=PRECISION_CHOICES, default="exact")
    history_retention_hours = models.PositiveIntegerField(default=168, validators=[MinValueValidator(1), MaxValueValidator(720)])
    live_visibility_minutes = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1), MaxValueValidator(720)])

    class Meta:
        db_table = "location_share_settings"

    def __str__(self):
        return f"Location settings: {self.user}"


class FamilyLocationPermission(TimeStampedModel):
    PRECISION_MODE_CHOICES = [
        ("inherit", "Inherit"),
        ("exact", "Exact"),
        ("approximate", "Approximate"),
    ]

    family_link = models.OneToOneField(
        FamilyLink,
        on_delete=models.CASCADE,
        related_name="location_permission",
    )
    can_view_live = models.BooleanField(default=True)
    can_view_history = models.BooleanField(default=True)
    can_view_battery = models.BooleanField(default=True)
    can_view_speed = models.BooleanField(default=True)
    history_window_hours = models.PositiveIntegerField(default=24, validators=[MinValueValidator(1), MaxValueValidator(168)])
    precision_mode = models.CharField(max_length=20, choices=PRECISION_MODE_CHOICES, default="inherit")

    class Meta:
        db_table = "family_location_permissions"

    def __str__(self):
        return f"Location permission for {self.family_link}"


class UserLocationPing(TimeStampedModel):
    SOURCE_CHOICES = [
        ("gps", "GPS"),
        ("network", "Network"),
        ("passive", "Passive"),
        ("manual", "Manual"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location_pings",
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy_m = models.FloatField(null=True, blank=True)
    altitude_m = models.FloatField(null=True, blank=True)
    speed_kmh = models.FloatField(null=True, blank=True)
    heading_deg = models.FloatField(null=True, blank=True)
    battery_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_charging = models.BooleanField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="gps")
    is_mocked = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "user_location_pings"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["user", "-recorded_at"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self):
        return f"{self.user} @ ({self.latitude}, {self.longitude})"


class UserGeofence(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="geofences",
    )
    name = models.CharField(max_length=100)
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_m = models.PositiveIntegerField(validators=[MinValueValidator(50), MaxValueValidator(5000)])
    notify_on_enter = models.BooleanField(default=True)
    notify_on_exit = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "user_geofences"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user})"


class GeofenceEvent(TimeStampedModel):
    EVENT_CHOICES = [
        ("enter", "Enter"),
        ("exit", "Exit"),
    ]

    geofence = models.ForeignKey(
        UserGeofence,
        on_delete=models.CASCADE,
        related_name="events",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="geofence_events",
    )
    ping = models.ForeignKey(
        UserLocationPing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="geofence_events",
    )
    event_type = models.CharField(max_length=10, choices=EVENT_CHOICES)
    distance_m = models.FloatField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "geofence_events"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["user", "-occurred_at"]),
            models.Index(fields=["geofence", "-occurred_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.geofence.name} - {self.user}"
