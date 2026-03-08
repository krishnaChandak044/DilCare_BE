"""
Steps — Serializers for step tracking endpoints.
"""
from rest_framework import serializers
from .models import StepGoal, DailyStepLog, StepEntry


class StepGoalSerializer(serializers.ModelSerializer):
    """Serializer for step goal management."""
    class Meta:
        model = StepGoal
        fields = [
            'id',
            'daily_goal',
            'stride_length_cm',
            'calories_per_step',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyStepLogSerializer(serializers.ModelSerializer):
    """Serializer for daily step log."""
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = DailyStepLog
        fields = [
            'id',
            'date',
            'total_steps',
            'manual_steps',
            'synced_steps',
            'goal_steps',
            'goal_met',
            'calories_burned',
            'distance_km',
            'active_minutes',
            'source',
            'progress_percent',
        ]
        read_only_fields = fields

    def get_progress_percent(self, obj):
        """Calculate completion percentage."""
        if obj.goal_steps == 0:
            return 0.0
        return round(min((obj.total_steps / obj.goal_steps) * 100, 100), 1)


class StepEntrySerializer(serializers.ModelSerializer):
    """Serializer for individual step entries."""
    source_display = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:
        model = StepEntry
        fields = [
            'id',
            'date',
            'steps',
            'source',
            'source_display',
            'notes',
            'recorded_at',
            'created_at',
        ]
        read_only_fields = ['id', 'date', 'created_at']


class AddManualStepsSerializer(serializers.Serializer):
    """Serializer for adding manual steps."""
    steps = serializers.IntegerField(min_value=1, max_value=100000)
    notes = serializers.CharField(max_length=200, required=False, default='')

    def validate_steps(self, value):
        if value <= 0:
            raise serializers.ValidationError("Steps must be a positive number.")
        return value


class StepStatsSerializer(serializers.Serializer):
    """Aggregated step statistics."""
    # Today
    today_steps = serializers.IntegerField()
    today_goal = serializers.IntegerField()
    today_progress = serializers.FloatField()
    today_calories = serializers.FloatField()
    today_distance_km = serializers.FloatField()
    today_active_minutes = serializers.IntegerField()
    
    # Streaks
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    
    # Period stats
    week_total_steps = serializers.IntegerField()
    week_avg_steps = serializers.IntegerField()
    week_days_goal_met = serializers.IntegerField()
    
    month_total_steps = serializers.IntegerField()
    month_avg_steps = serializers.IntegerField()
    month_days_goal_met = serializers.IntegerField()


class WeeklyChartSerializer(serializers.Serializer):
    """Weekly chart data."""
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.IntegerField())
    goals = serializers.ListField(child=serializers.IntegerField())
