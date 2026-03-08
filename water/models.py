"""
Water — Models for daily water intake tracking.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import SoftDeleteModel


class WaterGoal(SoftDeleteModel):
    """
    User's daily water intake goal.
    One active goal per user at a time.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="water_goals",
    )
    daily_glasses = models.PositiveSmallIntegerField(default=8)
    glass_size_ml = models.PositiveIntegerField(default=250, help_text="Size of one glass in ml")
    reminder_enabled = models.BooleanField(default=False)
    reminder_interval_hours = models.PositiveSmallIntegerField(
        default=2, 
        help_text="Hours between reminders"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.daily_glasses} glasses/day"

    @property
    def daily_target_ml(self):
        """Total daily target in ml."""
        return self.daily_glasses * self.glass_size_ml

    def save(self, *args, **kwargs):
        # Ensure only one active goal per user
        if self.is_active:
            WaterGoal.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class DailyWaterLog(SoftDeleteModel):
    """
    Tracks daily water intake for a user.
    One record per user per day.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="water_logs",
    )
    date = models.DateField()
    glasses = models.PositiveSmallIntegerField(default=0)
    goal_glasses = models.PositiveSmallIntegerField(default=8, help_text="Goal at time of logging")
    glass_size_ml = models.PositiveIntegerField(default=250)
    goal_reached = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date"]
        unique_together = ["user", "date"]

    def __str__(self):
        return f"{self.user.email} - {self.date}: {self.glasses}/{self.goal_glasses}"

    @property
    def total_ml(self):
        """Total water consumed in ml."""
        return self.glasses * self.glass_size_ml

    @property
    def progress_percent(self):
        """Progress as percentage."""
        if self.goal_glasses == 0:
            return 100
        return min(round((self.glasses / self.goal_glasses) * 100, 1), 100)

    def add_glass(self, count=1):
        """Add glasses and check if goal reached."""
        self.glasses += count
        if self.glasses >= self.goal_glasses and not self.goal_reached:
            self.goal_reached = True
        self.save(update_fields=["glasses", "goal_reached", "updated_at"])

    def remove_glass(self, count=1):
        """Remove glasses (minimum 0)."""
        self.glasses = max(0, self.glasses - count)
        self.goal_reached = self.glasses >= self.goal_glasses
        self.save(update_fields=["glasses", "goal_reached", "updated_at"])


class WaterIntakeEntry(SoftDeleteModel):
    """
    Individual water intake entries for detailed tracking.
    Optional - for users who want to log exact times.
    """
    daily_log = models.ForeignKey(
        DailyWaterLog,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    glasses = models.PositiveSmallIntegerField(default=1)
    logged_at = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-logged_at"]

    def __str__(self):
        return f"{self.glasses} glasses at {self.logged_at.strftime('%H:%M')}"
