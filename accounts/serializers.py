"""
Accounts — DRF Serializers for auth and profile.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Handles user registration with email + password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=150, required=False, default="")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        name = validated_data.pop("name", "")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )
        if name:
            parts = name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""
            user.save(update_fields=["first_name", "last_name"])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Read/write serializer for user profile data."""
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "first_name", "last_name",
            "phone", "age", "address", "emergency_contact", "blood_group",
            "parent_link_code",
        ]
        read_only_fields = ["id", "email", "parent_link_code"]

    def get_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or ""

    def update(self, instance, validated_data):
        # Allow frontend to send a `name` field directly
        name = self.initial_data.get("name")
        if name is not None:
            parts = name.split(" ", 1)
            instance.first_name = parts[0]
            instance.last_name = parts[1] if len(parts) > 1 else ""
        return super().update(instance, validated_data)


class LinkCodeSerializer(serializers.ModelSerializer):
    """Returns the user's parent link code."""
    class Meta:
        model = User
        fields = ["parent_link_code"]
        read_only_fields = ["parent_link_code"]
