"""
Family — Models for family linking (child monitors parent's health).
"""
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


class FamilyLink(SoftDeleteModel):
    """
    Links a child user to a parent user for health monitoring.
    The child can view the parent's health data.
    """
    RELATIONSHIP_CHOICES = [
        ("father", "Father"),
        ("mother", "Mother"),
        ("grandfather", "Grandfather"),
        ("grandmother", "Grandmother"),
        ("guardian", "Guardian"),
        ("other", "Other"),
    ]

    child = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="linked_parents",
        help_text="The user monitoring the parent's health (child)",
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="linked_children",
        help_text="The user being monitored (parent)",
    )
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default="other",
    )
    is_active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-linked_at"]
        unique_together = ["child", "parent"]

    def __str__(self):
        return f"{self.child.email} monitors {self.parent.email} ({self.relationship})"
