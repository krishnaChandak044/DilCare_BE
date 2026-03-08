"""
Water — Admin configuration for water models.
"""
from django.contrib import admin
from .models import WaterGoal, DailyWaterLog, WaterIntakeEntry


@admin.register(WaterGoal)
class WaterGoalAdmin(admin.ModelAdmin):
    list_display = ["user", "daily_glasses", "glass_size_ml", "reminder_enabled", "is_active", "created_at"]
    list_filter = ["is_active", "reminder_enabled", "created_at"]
    search_fields = ["user__email", "user__full_name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(DailyWaterLog)
class DailyWaterLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "glasses", "goal_glasses", "goal_reached", "created_at"]
    list_filter = ["goal_reached", "date"]
    search_fields = ["user__email", "user__full_name"]
    ordering = ["-date"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "date"


@admin.register(WaterIntakeEntry)
class WaterIntakeEntryAdmin(admin.ModelAdmin):
    list_display = ["daily_log", "glasses", "logged_at", "created_at"]
    list_filter = ["logged_at"]
    ordering = ["-logged_at"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("daily_log", "daily_log__user")
