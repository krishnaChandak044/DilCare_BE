from django.contrib import admin
from .models import WellnessTip, TipInteraction


@admin.register(WellnessTip)
class WellnessTipAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "duration", "is_active", "order", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("title", "description")
    ordering = ("order", "-created_at")
    list_editable = ("order", "is_active")


@admin.register(TipInteraction)
class TipInteractionAdmin(admin.ModelAdmin):
    list_display = ("user", "tip", "completed", "favorite")
    list_filter = ("completed", "favorite")
