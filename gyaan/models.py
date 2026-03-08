"""
Gyaan — Models for wellness tips, favourites and completions.
"""
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


class WellnessTip(SoftDeleteModel):
    """
    A wellness / Gyaan tip authored by admins.
    """
    CATEGORY_CHOICES = [
        ("nutrition", "Nutrition"),
        ("exercise", "Exercise"),
        ("meditation", "Meditation"),
        ("ayurveda", "Ayurveda"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Short summary shown in the card")
    content = models.TextField(blank=True, help_text="Full article / details")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=30, blank=True, help_text="Ionicons icon name")
    duration = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Duration in minutes (for timers, e.g. meditation)"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower = shown first")

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "Wellness Tip"
        verbose_name_plural = "Wellness Tips"

    def __str__(self):
        return f"[{self.category}] {self.title}"


class TipInteraction(models.Model):
    """
    Per-user interaction with a tip: completed / favourited.
    One row per (user, tip) pair.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tip_interactions",
    )
    tip = models.ForeignKey(
        WellnessTip,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    completed = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    favorited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "tip")
        verbose_name = "Tip Interaction"
        verbose_name_plural = "Tip Interactions"

    def __str__(self):
        return f"{self.user} — {self.tip.title}"
