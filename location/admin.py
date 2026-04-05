from django.contrib import admin

from .models import (
    FamilyLocationPermission,
    GeofenceEvent,
    LocationShareSetting,
    UserGeofence,
    UserLocationPing,
)


@admin.register(LocationShareSetting)
class LocationShareSettingAdmin(admin.ModelAdmin):
    list_display = ("user", "sharing_enabled", "share_precision", "history_retention_hours", "live_visibility_minutes")
    search_fields = ("user__email",)


@admin.register(FamilyLocationPermission)
class FamilyLocationPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "family_link",
        "can_view_live",
        "can_view_history",
        "history_window_hours",
        "precision_mode",
    )
    list_filter = ("can_view_live", "can_view_history", "precision_mode")


@admin.register(UserLocationPing)
class UserLocationPingAdmin(admin.ModelAdmin):
    list_display = ("user", "latitude", "longitude", "source", "battery_level", "recorded_at")
    list_filter = ("source", "is_mocked", "is_charging")
    search_fields = ("user__email",)


@admin.register(UserGeofence)
class UserGeofenceAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "radius_m", "is_active", "notify_on_enter", "notify_on_exit")
    list_filter = ("is_active", "notify_on_enter", "notify_on_exit")
    search_fields = ("user__email", "name")


@admin.register(GeofenceEvent)
class GeofenceEventAdmin(admin.ModelAdmin):
    list_display = ("user", "geofence", "event_type", "distance_m", "occurred_at")
    list_filter = ("event_type",)
    search_fields = ("user__email", "geofence__name")
