"""
Health — DRF Serializers for health readings.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

from .models import HealthReading, HealthGoal


class HealthReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for health readings.
    Handles both create and read operations.
    """
    # Map to frontend field names
    type = serializers.CharField(source='reading_type')
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = HealthReading
        fields = [
            'id', 'type', 'value', 'unit', 'status',
            'date', 'time', 'notes', 'recorded_at', 'created_at',
        ]
        read_only_fields = ['id', 'unit', 'status', 'date', 'time', 'created_at']

    def get_date(self, obj):
        """Format date for frontend display."""
        return obj.recorded_at.strftime('%d %b %Y')

    def get_time(self, obj):
        """Format time for frontend display."""
        return obj.recorded_at.strftime('%I:%M %p')


class HealthReadingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating health readings.
    Accepts frontend format and converts to backend format.
    """
    type = serializers.ChoiceField(
        choices=[t[0] for t in HealthReading.READING_TYPES],
        source='reading_type'
    )
    recorded_at = serializers.DateTimeField(required=False)

    class Meta:
        model = HealthReading
        fields = ['type', 'value', 'notes', 'recorded_at']

    def validate_value(self, value):
        """Validate value format based on reading type."""
        reading_type = self.initial_data.get('type')
        
        if reading_type == 'bp':
            # BP should be in format "120/80"
            if '/' not in value:
                raise serializers.ValidationError(
                    "Blood pressure should be in format 'systolic/diastolic' (e.g., 120/80)"
                )
            try:
                parts = value.split('/')
                systolic = float(parts[0].strip())
                diastolic = float(parts[1].strip())
                if systolic <= 0 or diastolic <= 0:
                    raise serializers.ValidationError("Values must be positive numbers")
                if systolic > 300 or diastolic > 200:
                    raise serializers.ValidationError("Values seem unrealistic")
            except (ValueError, IndexError):
                raise serializers.ValidationError("Invalid blood pressure format")
        else:
            # Other readings should be numeric
            try:
                val = float(value.strip())
                if val <= 0:
                    raise serializers.ValidationError("Value must be a positive number")
                
                # Realistic value checks
                if reading_type == 'sugar' and val > 600:
                    raise serializers.ValidationError("Blood sugar value seems unrealistic")
                if reading_type == 'heartRate' and (val < 20 or val > 250):
                    raise serializers.ValidationError("Heart rate value seems unrealistic")
                if reading_type == 'weight' and (val < 1 or val > 500):
                    raise serializers.ValidationError("Weight value seems unrealistic")
            except ValueError:
                raise serializers.ValidationError("Value must be a number")
        
        return value

    def create(self, validated_data):
        """Create a health reading with the current user."""
        validated_data['user'] = self.context['request'].user
        if 'recorded_at' not in validated_data or not validated_data['recorded_at']:
            validated_data['recorded_at'] = timezone.now()
        return super().create(validated_data)


class HealthSummarySerializer(serializers.Serializer):
    """
    Serializer for health summary - latest reading of each type.
    """
    type = serializers.CharField()
    value = serializers.CharField()
    unit = serializers.CharField()
    status = serializers.CharField()
    recorded_at = serializers.DateTimeField()
    date = serializers.CharField()
    time = serializers.CharField()


class HealthGoalSerializer(serializers.ModelSerializer):
    """Serializer for health goals."""
    type = serializers.CharField(source='reading_type')

    class Meta:
        model = HealthGoal
        fields = ['id', 'type', 'min_value', 'max_value', 'target_value']
        read_only_fields = ['id']


class HealthTrendSerializer(serializers.Serializer):
    """Serializer for weekly/monthly trend data."""
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.FloatField(allow_null=True))
    reading_type = serializers.CharField()
