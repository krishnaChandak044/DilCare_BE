from django.contrib import admin
from .models import EmergencyContact, SOSAlert


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "phone", "relationship", "is_primary", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("user__email", "name", "phone")


@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "latitude", "longitude", "resolved", "created_at")
    list_filter = ("resolved",)
    search_fields = ("user__email",)
