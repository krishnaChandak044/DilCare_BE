"""
Accounts — DRF Serializers for auth and profile.
Enhanced with better validation and new serializers for settings/devices.
"""
import re
from django.db import transaction
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import UserSettings, UserDevice

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Handles user registration with email + password.
    Optionally creates a family group atomically if family_name is provided.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=150, required=False, default="")
    family_name = serializers.CharField(max_length=100, required=False, default="")

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        name = validated_data.pop("name", "")
        family_name = validated_data.pop("family_name", "")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        if name:
            parts = name.strip().split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""
            user.save(update_fields=["first_name", "last_name"])

        # Atomically create family if name provided
        if family_name.strip():
            from family.models import Family, FamilyMembership
            family = Family.objects.create(
                name=family_name.strip(),
                created_by=user,
            )
            FamilyMembership.objects.create(
                family=family,
                user=user,
                role="admin",
            )

        return user


class UserSettingsSerializer(serializers.ModelSerializer):
    """Read/write serializer for user settings."""

    class Meta:
        model = UserSettings
        fields = [
            "language",
            "notifications_enabled",
            "medicine_reminders",
            "appointment_reminders",
            "health_tips_enabled",
            "dark_mode",
            "units",
            "daily_step_goal",
            "daily_water_goal",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Read/write serializer for user profile data."""
    name = serializers.SerializerMethodField()
    settings = UserSettingsSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "first_name", "last_name",
            "phone", "age", "address", "emergency_contact", "blood_group",
            "parent_link_code", "date_joined", "settings",
        ]
        read_only_fields = ["id", "email", "parent_link_code", "date_joined"]

    def get_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or ""

    def validate_phone(self, value):
        """Validate phone number format."""
        if value:
            # Remove spaces, dashes, parentheses
            cleaned = re.sub(r'[\s\-\(\)]', '', value)
            if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
                raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_age(self, value):
        """Validate age is a reasonable number."""
        if value:
            try:
                age_int = int(value)
                if age_int < 1 or age_int > 120:
                    raise serializers.ValidationError("Enter a valid age between 1 and 120.")
            except ValueError:
                raise serializers.ValidationError("Age must be a number.")
        return value

    def validate_blood_group(self, value):
        """Validate blood group format."""
        if value:
            valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if value.upper() not in valid_blood_groups:
                raise serializers.ValidationError(
                    f"Invalid blood group. Must be one of: {', '.join(valid_blood_groups)}"
                )
            return value.upper()
        return value

    def update(self, instance, validated_data):
        # Allow frontend to send a `name` field directly
        name = self.initial_data.get("name")
        if name is not None:
            parts = name.strip().split(" ", 1)
            instance.first_name = parts[0]
            instance.last_name = parts[1] if len(parts) > 1 else ""
        return super().update(instance, validated_data)


class LinkCodeSerializer(serializers.ModelSerializer):
    """Returns the user's parent link code."""
    class Meta:
        model = User
        fields = ["parent_link_code"]
        read_only_fields = ["parent_link_code"]


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for registering device tokens."""

    class Meta:
        model = UserDevice
        fields = ["id", "device_token", "device_type", "device_name", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]

    def validate_device_type(self, value):
        valid_types = ['ios', 'android', 'web']
        if value.lower() not in valid_types:
            raise serializers.ValidationError(f"Device type must be one of: {', '.join(valid_types)}")
        return value.lower()

    def create(self, validated_data):
        user = self.context['request'].user
        # Update or create - if token exists, reactivate it
        device, created = UserDevice.objects.update_or_create(
            user=user,
            device_token=validated_data['device_token'],
            defaults={
                'device_type': validated_data['device_type'],
                'device_name': validated_data.get('device_name', ''),
                'is_active': True,
            }
        )
        return device


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout - accepts refresh token to blacklist."""
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
