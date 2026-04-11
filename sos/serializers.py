"""
SOS — Serializers.
"""
from rest_framework import serializers
from .models import EmergencyContact, SOSAlert


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = [
            "id", "name", "phone", "relationship",
            "is_primary", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CreateEmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ["name", "phone", "relationship", "is_primary"]

    def validate_phone(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Phone number is too short.")
        return value.strip()


class SOSAlertSerializer(serializers.ModelSerializer):
    notified_contacts = EmergencyContactSerializer(many=True, read_only=True)

    class Meta:
        model = SOSAlert
        fields = [
            "id", "latitude", "longitude",
            "resolved", "resolved_at",
            "notified_contacts", "created_at",
        ]
        read_only_fields = ["id", "resolved", "resolved_at", "notified_contacts", "created_at"]


class TriggerSOSSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)   
    location_address = serializers.CharField(required=False, default="Unknown location")