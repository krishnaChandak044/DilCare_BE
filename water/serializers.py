"""
Water — Serializers for water intake tracking.
"""
from rest_framework import serializers
from .models import WaterGoal, DailyWaterLog, WaterIntakeEntry


class WaterGoalSerializer(serializers.ModelSerializer):
    """Serializer for WaterGoal CRUD operations."""
    daily_target_ml = serializers.ReadOnlyField()

    class Meta:
        model = WaterGoal
        fields = [
            "id",
            "daily_glasses",
            "glass_size_ml",
            "daily_target_ml",
            "reminder_enabled",
            "reminder_interval_hours",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_daily_glasses(self, value):
        """Validate daily glasses is reasonable."""
        if value < 1:
            raise serializers.ValidationError("Daily glasses must be at least 1.")
        if value > 30:
            raise serializers.ValidationError("Daily glasses cannot exceed 30.")
        return value

    def validate_glass_size_ml(self, value):
        """Validate glass size is reasonable."""
        if value < 50:
            raise serializers.ValidationError("Glass size must be at least 50ml.")
        if value > 1000:
            raise serializers.ValidationError("Glass size cannot exceed 1000ml.")
        return value


class WaterIntakeEntrySerializer(serializers.ModelSerializer):
    """Serializer for individual water intake entries."""

    class Meta:
        model = WaterIntakeEntry
        fields = [
            "id",
            "glasses",
            "logged_at",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DailyWaterLogSerializer(serializers.ModelSerializer):
    """Serializer for DailyWaterLog."""
    total_ml = serializers.ReadOnlyField()
    progress_percent = serializers.ReadOnlyField()
    entries = WaterIntakeEntrySerializer(many=True, read_only=True)

    class Meta:
        model = DailyWaterLog
        fields = [
            "id",
            "date",
            "glasses",
            "goal_glasses",
            "glass_size_ml",
            "total_ml",
            "progress_percent",
            "goal_reached",
            "entries",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_ml", "progress_percent", "goal_reached", "entries", "created_at", "updated_at"]


class TodayWaterSerializer(serializers.Serializer):
    """
    Serializer for today's water data.
    Combines current intake with goal info.
    """
    date = serializers.DateField()
    glasses = serializers.IntegerField()
    goal_glasses = serializers.IntegerField()
    glass_size_ml = serializers.IntegerField()
    total_ml = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    goal_reached = serializers.BooleanField()
    streak = serializers.IntegerField()
    reminder_enabled = serializers.BooleanField()


class AddGlassSerializer(serializers.Serializer):
    """Serializer for adding/removing glasses."""
    count = serializers.IntegerField(default=1, min_value=1, max_value=10)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=200)


class WaterHistorySerializer(serializers.Serializer):
    """Serializer for water history/trends."""
    date = serializers.DateField()
    glasses = serializers.IntegerField()
    goal_glasses = serializers.IntegerField()
    total_ml = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    goal_reached = serializers.BooleanField()


class WaterStatsSerializer(serializers.Serializer):
    """Serializer for water statistics."""
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    total_glasses_7d = serializers.IntegerField()
    total_glasses_30d = serializers.IntegerField()
    avg_glasses_7d = serializers.FloatField()
    avg_glasses_30d = serializers.FloatField()
    goals_met_7d = serializers.IntegerField()
    goals_met_30d = serializers.IntegerField()
