"""
Family — Serializers for family linking functionality.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FamilyLink

User = get_user_model()


class ParentSummarySerializer(serializers.ModelSerializer):
    """Minimal parent info for family listing."""
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "age", "blood_group"]
        read_only_fields = fields


class FamilyLinkSerializer(serializers.ModelSerializer):
    """Serializer for FamilyLink with nested parent info."""
    parent_info = ParentSummarySerializer(source="parent", read_only=True)
    relationship_display = serializers.CharField(source="get_relationship_display", read_only=True)

    class Meta:
        model = FamilyLink
        fields = [
            "id",
            "parent",
            "parent_info",
            "relationship",
            "relationship_display",
            "is_active",
            "linked_at",
            "created_at",
        ]
        read_only_fields = ["id", "parent_info", "linked_at", "created_at"]


class LinkParentSerializer(serializers.Serializer):
    """Serializer for linking to a parent via link code."""
    link_code = serializers.CharField(max_length=6, min_length=6)
    relationship = serializers.ChoiceField(
        choices=FamilyLink.RELATIONSHIP_CHOICES,
        default="other",
    )

    def validate_link_code(self, value):
        """Validate the link code exists."""
        value = value.upper()
        try:
            User.objects.get(parent_link_code=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid link code. Please check and try again.")
        return value


class ParentHealthSummarySerializer(serializers.Serializer):
    """
    Aggregated health summary for a linked parent.
    Returned when child requests parent's health overview.
    """
    # Parent info
    parent_id = serializers.UUIDField()
    parent_name = serializers.CharField()
    relationship = serializers.CharField()
    
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
    
    # Overall status
    overall_status = serializers.CharField()  # good, warning, danger
    last_activity = serializers.DateTimeField(allow_null=True)
