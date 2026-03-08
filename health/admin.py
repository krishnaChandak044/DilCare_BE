"""
Health — Admin configuration for health readings.
"""
from django.contrib import admin
from .models import HealthReading, HealthGoal


@admin.register(HealthReading)
class HealthReadingAdmin(admin.ModelAdmin):
    """Admin for health readings."""
    list_display = ('user', 'reading_type', 'value', 'status', 'recorded_at', 'created_at')
    list_filter = ('reading_type', 'status', 'recorded_at', 'is_deleted')
    search_fields = ('user__email', 'value', 'notes')
    ordering = ('-recorded_at',)
    date_hierarchy = 'recorded_at'
    readonly_fields = ('id', 'value_primary', 'value_secondary', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'reading_type', 'value', 'unit', 'status')}),
        ('Parsed Values', {'fields': ('value_primary', 'value_secondary'), 'classes': ('collapse',)}),
        ('Details', {'fields': ('notes', 'recorded_at')}),
        ('Meta', {'fields': ('id', 'is_deleted', 'deleted_at', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(HealthGoal)
class HealthGoalAdmin(admin.ModelAdmin):
    """Admin for health goals."""
    list_display = ('user', 'reading_type', 'min_value', 'max_value', 'target_value')
    list_filter = ('reading_type',)
    search_fields = ('user__email',)
