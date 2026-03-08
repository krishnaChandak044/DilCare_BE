"""
SOS — Models for emergency contacts and SOS alerts.
"""
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


class EmergencyContact(SoftDeleteModel):
    """
    A personal emergency contact for the user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "-created_at"]
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"

    def save(self, *args, **kwargs):
        # Ensure only one primary per user
        if self.is_primary:
            EmergencyContact.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone}) — {self.user}"


class SOSAlert(SoftDeleteModel):
    """
    Log of every SOS trigger by a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sos_alerts",
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notified_contacts = models.ManyToManyField(EmergencyContact, blank=True, related_name="sos_notifications")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SOS Alert"
        verbose_name_plural = "SOS Alerts"

    def __str__(self):
        return f"SOS by {self.user} at {self.created_at:%Y-%m-%d %H:%M}"
