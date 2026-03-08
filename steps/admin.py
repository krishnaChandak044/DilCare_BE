"""
Steps — Admin configuration
"""
from django.contrib import admin
from .models import StepGoal, DailyStepLog, StepEntry


@admin.register(StepGoal)
class StepGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_goal', 'stride_length_cm', 'calories_per_step', 'created_at')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DailyStepLog)
class DailyStepLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_steps', 'manual_steps', 'synced_steps', 'goal_steps', 'goal_met', 'calories_burned')
    list_filter = ('date', 'goal_met', 'source')
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    readonly_fields = ('total_steps', 'calories_burned', 'distance_km', 'active_minutes', 'created_at', 'updated_at')
    date_hierarchy = 'date'


@admin.register(StepEntry)
class StepEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'steps', 'source', 'notes', 'recorded_at')
    list_filter = ('date', 'source')
    search_fields = ('user__email', 'notes')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
