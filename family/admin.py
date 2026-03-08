"""
Family — Admin configuration
"""
from django.contrib import admin
from .models import FamilyLink


@admin.register(FamilyLink)
class FamilyLinkAdmin(admin.ModelAdmin):
    list_display = ("child", "parent", "relationship", "is_active", "linked_at")
    list_filter = ("relationship", "is_active", "linked_at")
    search_fields = ("child__email", "parent__email")
    raw_id_fields = ("child", "parent")
    readonly_fields = ("linked_at",)

