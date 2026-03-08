"""
Accounts — Admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSettings, UserDevice


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the email-based User model."""
    list_display = ("email", "first_name", "last_name", "parent_link_code", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("email", "first_name", "last_name", "parent_link_code", "phone")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone", "age", "address", "emergency_contact", "blood_group")}),
        ("Family", {"fields": ("parent_link_code",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """Admin for user settings."""
    list_display = ("user", "language", "notifications_enabled", "dark_mode", "units", "updated_at")
    list_filter = ("language", "notifications_enabled", "dark_mode", "units")
    search_fields = ("user__email",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    """Admin for user devices (FCM tokens)."""
    list_display = ("user", "device_type", "device_name", "is_active", "last_used_at")
    list_filter = ("device_type", "is_active")
    search_fields = ("user__email", "device_name")
    readonly_fields = ("created_at", "last_used_at")
