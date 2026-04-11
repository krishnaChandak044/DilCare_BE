from decimal import Decimal

from rest_framework import serializers

from family.models import FamilyLink

from .models import (
    FamilyLocationPermission,
    GeofenceEvent,
    LocationShareSetting,
    UserGeofence,
    UserLocationPing,
)


class LocationShareSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationShareSetting
        fields = [
            "sharing_enabled",
            "share_precision",
            "history_retention_hours",
            "live_visibility_minutes",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class FamilyLocationPermissionSerializer(serializers.ModelSerializer):
    child_id = serializers.IntegerField(source="family_link.child_id", read_only=True)
    child_name = serializers.SerializerMethodField()
    relationship = serializers.CharField(source="family_link.get_relationship_display", read_only=True)

    class Meta:
        model = FamilyLocationPermission
        fields = [
            "id",
            "family_link",
            "child_id",
            "child_name",
            "relationship",
            "can_view_live",
            "can_view_history",
            "can_view_battery",
            "can_view_speed",
            "history_window_hours",
            "precision_mode",
            "updated_at",
        ]
        read_only_fields = ["id", "family_link", "child_id", "child_name", "relationship", "updated_at"]

    def get_child_name(self, obj):
        child = obj.family_link.child
        return child.get_full_name() or child.email


class UserLocationPingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocationPing
        fields = [
            "latitude",
            "longitude",
            "accuracy_m",
            "altitude_m",
            "speed_kmh",
            "heading_deg",
            "battery_level",
            "is_charging",
            "source",
            "is_mocked",
            "recorded_at",
        ]


class UserLocationPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocationPing
        fields = [
            "id",
            "latitude",
            "longitude",
            "accuracy_m",
            "altitude_m",
            "speed_kmh",
            "heading_deg",
            "battery_level",
            "is_charging",
            "source",
            "is_mocked",
            "recorded_at",
        ]


class UserGeofenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGeofence
        fields = [
            "id",
            "name",
            "center_latitude",
            "center_longitude",
            "radius_m",
            "notify_on_enter",
            "notify_on_exit",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GeofenceEventSerializer(serializers.ModelSerializer):
    geofence_name = serializers.CharField(source="geofence.name", read_only=True)

    class Meta:
        model = GeofenceEvent
        fields = [
            "id",
            "geofence",
            "geofence_name",
            "event_type",
            "distance_m",
            "occurred_at",
        ]


class FamilyLiveLocationSerializer(serializers.Serializer):
    """Live ping for a family member (same Family group)."""
    member_id = serializers.IntegerField()
    member_name = serializers.CharField()
    parent_id = serializers.IntegerField(required=False)
    parent_name = serializers.CharField(required=False)
    phone = serializers.CharField(allow_blank=True, required=False, default="")
    nickname = serializers.CharField(allow_blank=True, required=False, default="")
    role = serializers.CharField(allow_blank=True, required=False, default="")
    relationship = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    accuracy_m = serializers.FloatField(allow_null=True)
    speed_kmh = serializers.FloatField(allow_null=True)
    battery_level = serializers.IntegerField(allow_null=True)
    is_charging = serializers.BooleanField(allow_null=True)
    recorded_at = serializers.DateTimeField()
    is_live = serializers.BooleanField()
    precision_applied = serializers.CharField()


class FamilyHistoryQuerySerializer(serializers.Serializer):
    hours = serializers.IntegerField(required=False, min_value=1, max_value=168, default=6)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=1000, default=200)


def apply_precision(latitude: Decimal, longitude: Decimal, precision: str):
    if precision == "approximate":
        return (
            Decimal(round(float(latitude), 2)).quantize(Decimal("0.01")),
            Decimal(round(float(longitude), 2)).quantize(Decimal("0.01")),
        )
    return latitude, longitude


def resolve_precision_mode(setting: LocationShareSetting, permission: FamilyLocationPermission):
    if permission.precision_mode == "inherit":
        return setting.share_precision
    return permission.precision_mode


def ensure_permission_for_link(link: FamilyLink):
    permission, _ = FamilyLocationPermission.objects.get_or_create(family_link=link)
    return permission
