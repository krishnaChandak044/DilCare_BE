"""
Medicine — Serializers for medicine and prescription management.
"""
import re
from rest_framework import serializers
from .models import Medicine, MedicineIntake, Prescription


class MedicineSerializer(serializers.ModelSerializer):
    """Serializer for Medicine CRUD operations."""
    time_list = serializers.ReadOnlyField()
    today_status = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = [
            "id",
            "name",
            "dosage",
            "frequency",
            "instructions",
            "schedule_times",
            "time_list",
            "start_date",
            "end_date",
            "is_active",
            "reminder_enabled",
            "reminder_minutes_before",
            "today_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_schedule_times(self, value):
        """Validate that schedule_times contains valid HH:MM format times."""
        time_pattern = re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
        times = [t.strip() for t in value.split(",") if t.strip()]
        
        if not times:
            raise serializers.ValidationError("At least one schedule time is required.")
        
        for t in times:
            if not time_pattern.match(t):
                raise serializers.ValidationError(
                    f"Invalid time format: '{t}'. Use HH:MM format (e.g., 08:00, 14:30)."
                )
        
        return ",".join(times)  # Normalize

    def validate_name(self, value):
        """Ensure medicine name is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Medicine name is required.")
        return value.strip()

    def get_today_status(self, obj):
        """Get today's intake status for this medicine."""
        from django.utils import timezone
        today = timezone.localdate()
        
        intakes = obj.intakes.filter(scheduled_date=today)
        total = intakes.count()
        taken = intakes.filter(status="taken").count()
        missed = intakes.filter(status="missed").count()
        pending = intakes.filter(status="pending").count()
        
        return {
            "total": total,
            "taken": taken,
            "missed": missed,
            "pending": pending,
            "all_taken": total > 0 and taken == total,
        }


class MedicineIntakeSerializer(serializers.ModelSerializer):
    """Serializer for MedicineIntake tracking."""
    medicine_name = serializers.CharField(source="medicine.name", read_only=True)
    medicine_dosage = serializers.CharField(source="medicine.dosage", read_only=True)

    class Meta:
        model = MedicineIntake
        fields = [
            "id",
            "medicine",
            "medicine_name",
            "medicine_dosage",
            "scheduled_date",
            "scheduled_time",
            "status",
            "taken_at",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "taken_at", "created_at"]


class MedicineIntakeToggleSerializer(serializers.Serializer):
    """Serializer for toggling medicine intake status."""
    status = serializers.ChoiceField(
        choices=["taken", "missed", "skipped", "pending"],
        required=False,
        help_text="If not provided, toggles between 'taken' and 'pending'."
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription CRUD operations."""
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id",
            "name",
            "doctor_name",
            "hospital_name",
            "prescription_date",
            "file",
            "file_type",
            "file_url",
            "file_size",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "file_size", "created_at", "updated_at"]

    def validate_name(self, value):
        """Ensure prescription name is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Prescription name is required.")
        return value.strip()

    def get_file_size(self, obj):
        """Return file size in bytes if file exists."""
        if obj.file and hasattr(obj.file, 'size'):
            return obj.file.size
        return None


class TodayMedicineSerializer(serializers.Serializer):
    """
    Serializer for today's medicine schedule view.
    Combines medicine info with today's intake status.
    """
    id = serializers.UUIDField()
    name = serializers.CharField()
    dosage = serializers.CharField()
    frequency = serializers.CharField()
    time = serializers.CharField()
    taken = serializers.BooleanField()
    missed = serializers.BooleanField()
    intake_id = serializers.UUIDField(allow_null=True)


class MedicineSummarySerializer(serializers.Serializer):
    """Summary statistics for medicine adherence."""
    total_medicines = serializers.IntegerField()
    active_medicines = serializers.IntegerField()
    today_total = serializers.IntegerField()
    today_taken = serializers.IntegerField()
    today_missed = serializers.IntegerField()
    today_pending = serializers.IntegerField()
    adherence_rate_7d = serializers.FloatField()
    adherence_rate_30d = serializers.FloatField()
