"""
Family — Serializers for family group functionality.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Family, FamilyMembership

User = get_user_model()


class CreateFamilySerializer(serializers.Serializer):
    """POST /api/v1/family/create/ — create a new family group."""
    name = serializers.CharField(max_length=100, min_length=2)

    def validate_name(self, value):
        return value.strip()


class JoinFamilySerializer(serializers.Serializer):
    """POST /api/v1/family/join/ — join using invite code."""
    invite_code = serializers.CharField(max_length=6, min_length=6)
    nickname = serializers.CharField(max_length=50, required=False, default="")

    def validate_invite_code(self, value):
        code = value.upper().strip()
        if not Family.objects.filter(invite_code=code).exists():
            raise serializers.ValidationError("Invalid invite code. Please check and try again.")
        return code


class FamilyMemberSerializer(serializers.ModelSerializer):
    """Nested member info inside family response."""
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.SerializerMethodField()
    phone = serializers.CharField(source="user.phone", read_only=True)
    age = serializers.CharField(source="user.age", read_only=True)
    blood_group = serializers.CharField(source="user.blood_group", read_only=True)

    class Meta:
        model = FamilyMembership
        fields = [
            "id", "user_id", "email", "name", "phone", "age",
            "blood_group", "role", "nickname", "joined_at",
        ]
        read_only_fields = fields

    def get_name(self, obj):
        full = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full or obj.user.email


class FamilySerializer(serializers.ModelSerializer):
    """Full family response with members list."""
    members = FamilyMemberSerializer(source="memberships", many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    slots_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = Family
        fields = [
            "id", "name", "invite_code", "plan", "max_members",
            "member_count", "is_full", "slots_remaining", "members", "created_at",
        ]
        read_only_fields = fields


class UpgradePlanSerializer(serializers.Serializer):
    """POST /api/v1/family/upgrade/ — upgrade family plan."""
    PLAN_PRICING = {
        "free": {"price": 0, "label": "Free", "members": 4},
        "plus": {"price": 99, "label": "Plus", "members": 6},
        "premium": {"price": 199, "label": "Premium", "members": 10},
    }
    plan = serializers.ChoiceField(choices=Family.PLAN_CHOICES)

    def validate_plan(self, value):
        return value.lower().strip()


class FamilyMemberHealthSummarySerializer(serializers.Serializer):
    """Health summary for any family member."""
    # Member info
    member_id = serializers.IntegerField()
    member_name = serializers.CharField()
    nickname = serializers.CharField(allow_blank=True)

    # Latest readings
    latest_bp = serializers.CharField(allow_null=True)
    bp_status = serializers.CharField(allow_null=True)
    bp_recorded_at = serializers.DateTimeField(allow_null=True)

    latest_sugar = serializers.CharField(allow_null=True)
    sugar_status = serializers.CharField(allow_null=True)
    sugar_recorded_at = serializers.DateTimeField(allow_null=True)

    latest_heart_rate = serializers.IntegerField(allow_null=True)
    heart_rate_status = serializers.CharField(allow_null=True)
    heart_rate_recorded_at = serializers.DateTimeField(allow_null=True)

    # Medicine adherence
    medicines_today_total = serializers.IntegerField()
    medicines_today_taken = serializers.IntegerField()
    medicine_adherence_percent = serializers.FloatField()

    # Water intake
    water_glasses_today = serializers.IntegerField()
    water_goal_today = serializers.IntegerField()

    # Overall
    overall_status = serializers.CharField()
    last_activity = serializers.DateTimeField(allow_null=True)
