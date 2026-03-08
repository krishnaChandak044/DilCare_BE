"""
Medicine — Admin configuration for medicine models.
"""
from django.contrib import admin
from .models import Medicine, MedicineIntake, Prescription


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "dosage", "frequency", "is_active", "created_at"]
    list_filter = ["frequency", "is_active", "reminder_enabled", "created_at"]
    search_fields = ["name", "user__email", "user__full_name"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    
    fieldsets = (
        (None, {"fields": ("user", "name", "dosage", "frequency", "instructions")}),
        ("Schedule", {"fields": ("schedule_times", "start_date", "end_date", "is_active")}),
        ("Reminders", {"fields": ("reminder_enabled", "reminder_minutes_before")}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at")}),
    )


@admin.register(MedicineIntake)
class MedicineIntakeAdmin(admin.ModelAdmin):
    list_display = ["medicine", "scheduled_date", "scheduled_time", "status", "taken_at"]
    list_filter = ["status", "scheduled_date"]
    search_fields = ["medicine__name", "medicine__user__email"]
    ordering = ["-scheduled_date", "-scheduled_time"]
    readonly_fields = ["id", "created_at", "updated_at"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("medicine", "medicine__user")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "doctor_name", "prescription_date", "file_type", "created_at"]
    list_filter = ["file_type", "prescription_date", "created_at"]
    search_fields = ["name", "doctor_name", "user__email"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
    
    fieldsets = (
        (None, {"fields": ("user", "name", "doctor_name", "hospital_name", "prescription_date")}),
        ("File", {"fields": ("file", "file_type", "file_url")}),
        ("Notes", {"fields": ("notes",)}),
        ("Metadata", {"fields": ("id", "created_at", "updated_at")}),
    )
