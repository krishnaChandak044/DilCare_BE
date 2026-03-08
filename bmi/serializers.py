"""
BMI — Serializers.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import BMIRecord


class BMIRecordSerializer(serializers.ModelSerializer):
    """Full read serializer for a BMI record."""

    class Meta:
        model = BMIRecord
        fields = [
            "id",
            "weight",
            "height",
            "bmi",
            "category",
            "date",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "bmi", "category", "created_at"]


class CreateBMIRecordSerializer(serializers.ModelSerializer):
    """Write serializer for creating a BMI record; bmi & category auto-computed."""
    date = serializers.DateField(default=timezone.localdate)

    class Meta:
        model = BMIRecord
        fields = ["weight", "height", "date", "notes"]

    def validate_weight(self, value):
        if value <= 0 or value > 500:
            raise serializers.ValidationError("Weight must be between 0 and 500 kg.")
        return value

    def validate_height(self, value):
        if value <= 0 or value > 300:
            raise serializers.ValidationError("Height must be between 0 and 300 cm.")
        return value
