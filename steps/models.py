"""
Steps — Models for step tracking, goals, and achievements.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import SoftDeleteModel

User = get_user_model()


class StepGoal(SoftDeleteModel):
    """
    Daily step goal for a user.
    Only one active goal per user at a time.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='step_goal')
    daily_goal = models.PositiveIntegerField(default=10000)
    stride_length_cm = models.PositiveIntegerField(
        default=76,
        help_text="Average stride length in centimeters"
    )
    calories_per_step = models.FloatField(
        default=0.04,
        help_text="Estimated calories burned per step"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.daily_goal} steps/day"


class DailyStepLog(SoftDeleteModel):
    """
    Daily aggregated step data.
    One record per user per day.
    """
    SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('google_fit', 'Google Fit'),
        ('apple_health', 'Apple Health'),
        ('device', 'Wearable Device'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='step_logs')
    date = models.DateField(default=timezone.localdate)
    
    total_steps = models.PositiveIntegerField(default=0)
    manual_steps = models.PositiveIntegerField(default=0)
    synced_steps = models.PositiveIntegerField(default=0)
    
    goal_steps = models.PositiveIntegerField(default=10000)
    goal_met = models.BooleanField(default=False)
    
    # Computed stats (updated when steps change)
    calories_burned = models.FloatField(default=0.0)
    distance_km = models.FloatField(default=0.0)
    active_minutes = models.PositiveIntegerField(default=0)
    
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.date} — {self.total_steps} steps"

    def recalculate(self, step_goal=None):
        """Recalculate computed fields after step changes."""
        if step_goal is None:
            step_goal = StepGoal.objects.filter(user=self.user).first()
        
        cals_per_step = step_goal.calories_per_step if step_goal else 0.04
        stride_cm = step_goal.stride_length_cm if step_goal else 76
        goal = step_goal.daily_goal if step_goal else 10000
        
        self.goal_steps = goal
        self.calories_burned = round(self.total_steps * cals_per_step, 1)
        self.distance_km = round(self.total_steps * stride_cm / 100000, 2)
        self.active_minutes = self.total_steps // 100  # ~100 steps/min
        self.goal_met = self.total_steps >= goal

    def save(self, *args, **kwargs):
        self.total_steps = self.manual_steps + self.synced_steps
        if not kwargs.pop('skip_recalc', False):
            self.recalculate()
        super().save(*args, **kwargs)


class StepEntry(SoftDeleteModel):
    """
    Individual step entries — granular tracking.
    Multiple entries per day allowed (e.g., morning walk, evening walk).
    """
    SOURCE_CHOICES = DailyStepLog.SOURCE_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='step_entries')
    date = models.DateField(default=timezone.localdate)
    steps = models.PositiveIntegerField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    notes = models.CharField(max_length=200, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.steps} steps — {self.source} — {self.recorded_at}"
