"""
Medicine — Models for medicine tracking and prescription storage.
"""
import math
from datetime import date, timedelta
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel

#Comment added as per the issue 

class Medicine(SoftDeleteModel):
    """
    A medicine that a user takes regularly.
    Tracks dosage, frequency, schedule times, and daily intake status.
    """
    FREQUENCY_CHOICES = [
        ("once_daily", "Once Daily"),
        ("twice_daily", "Twice Daily"),
        ("thrice_daily", "Thrice Daily"),
        ("four_times", "Four Times Daily"),
        ("as_needed", "As Needed"),
        ("weekly", "Weekly"),
        ("custom", "Custom"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medicines",
    )
    name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100, blank=True, help_text="e.g., 500mg, 1 tablet")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="once_daily")
    instructions = models.TextField(blank=True, help_text="Special instructions like 'take with food'")
    
    # Schedule times (stored as HH:MM format, comma-separated for multiple times)
    schedule_times = models.CharField(
        max_length=100, 
        default="08:00",
        help_text="Comma-separated times in HH:MM format, e.g., '08:00,14:00,20:00'"
    )
    
    # Duration
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # ── Inventory tracking ────────────────────────────────────────
    current_quantity = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Number of pills/doses currently in stock"
    )
    doses_per_day = models.PositiveSmallIntegerField(
        default=1,
        help_text="How many doses/pills the user takes per day (auto-derived from schedule_times count)"
    )

    # Notification settings
    reminder_enabled = models.BooleanField(default=True)
    reminder_minutes_before = models.PositiveSmallIntegerField(default=15)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.dosage}) - {self.user.email}"

    @property
    def time_list(self):
        """Return schedule times as a list."""
        return [t.strip() for t in self.schedule_times.split(",") if t.strip()]

    @property
    def computed_doses_per_day(self):
        """Derive doses-per-day from schedule_times count."""
        return max(1, len(self.time_list))

    @property
    def inventory_end_date(self):
        """Compute the date on which the medicine will run out (None if no quantity set)."""
        if self.current_quantity is None:
            return None
        dpd = self.doses_per_day or self.computed_doses_per_day
        if dpd <= 0:
            return None
        days_left = math.floor(self.current_quantity / dpd)
        return date.today() + timedelta(days=days_left)

    @property
    def days_until_empty(self):
        """Days remaining until medicine runs out (None if no quantity)."""
        end = self.inventory_end_date
        if end is None:
            return None
        delta = (end - date.today()).days
        return max(0, delta)

    @property
    def is_running_low(self):
        """True when medicine will run out within 2 days."""
        d = self.days_until_empty
        return d is not None and d <= 2


class MedicineIntake(SoftDeleteModel):
    """
    Tracks when a user takes their medicine.
    One record per medicine per scheduled time per day.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("taken", "Taken"),
        ("missed", "Missed"),
        ("skipped", "Skipped"),
    ]

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name="intakes",
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    taken_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-scheduled_date", "-scheduled_time"]
        unique_together = ["medicine", "scheduled_date", "scheduled_time"]

    def __str__(self):
        return f"{self.medicine.name} - {self.scheduled_date} {self.scheduled_time} ({self.status})"

    def mark_taken(self):
        """Mark this intake as taken."""
        from django.utils import timezone
        self.status = "taken"
        self.taken_at = timezone.now()
        self.save(update_fields=["status", "taken_at"])

    def mark_missed(self):
        """Mark this intake as missed."""
        self.status = "missed"
        self.save(update_fields=["status"])


class Prescription(SoftDeleteModel):
    """
    Stores prescription documents/images uploaded by users.
    """
    FILE_TYPE_CHOICES = [
        ("image", "Image"),
        ("pdf", "PDF"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    name = models.CharField(max_length=200, help_text="Label for this prescription")
    doctor_name = models.CharField(max_length=150, blank=True)
    hospital_name = models.CharField(max_length=200, blank=True)
    prescription_date = models.DateField(null=True, blank=True)
    
    # File storage
    file = models.FileField(upload_to="prescriptions/%Y/%m/", null=True, blank=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default="image")
    file_url = models.URLField(max_length=500, blank=True, help_text="External URL if not uploaded")
    
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-prescription_date", "-created_at"]

    def __str__(self):
        return f"{self.name} - Dr. {self.doctor_name}" if self.doctor_name else self.name
