from django.contrib import admin
from .models import BMIRecord


@admin.register(BMIRecord)
class BMIRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "bmi", "category", "weight", "height", "date", "created_at")
    list_filter = ("category", "date")
    search_fields = ("user__email",)
    readonly_fields = ("bmi", "category", "created_at", "updated_at")
    ordering = ("-date",)
