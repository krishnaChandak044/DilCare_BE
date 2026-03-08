"""
Doctor — Serializers for doctors, appointments, and medical documents.
"""
from rest_framework import serializers
from .models import Doctor, Appointment, MedicalDocument


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for Doctor model."""
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    appointments_count = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id',
            'name',
            'specialty',
            'specialty_display',
            'phone',
            'email',
            'hospital',
            'address',
            'notes',
            'is_primary',
            'appointments_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_appointments_count(self, obj):
        """Count upcoming appointments with this doctor."""
        return obj.appointments.filter(status='scheduled', deleted_at__isnull=True).count()

    def validate(self, data):
        """Ensure only one primary doctor per user."""
        if data.get('is_primary', False):
            user = self.context['request'].user
            # Check if another doctor is already primary
            existing_primary = Doctor.objects.filter(
                user=user,
                is_primary=True,
                deleted_at__isnull=True
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing_primary.exists():
                # Unset the previous primary
                existing_primary.update(is_primary=False)
        
        return data


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for appointment lists."""
    doctor_name = serializers.CharField()
    specialty = serializers.CharField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'specialty',
            'appointment_date',
            'appointment_time',
            'reason',
            'status',
            'status_display',
            'location',
        ]
        read_only_fields = ['id', 'doctor_name', 'specialty']


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for appointment CRUD operations."""
    doctor_name = serializers.CharField(read_only=True)
    specialty = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'specialty',
            'appointment_date',
            'appointment_time',
            'reason',
            'location',
            'status',
            'status_display',
            'notes',
            'reminder_sent',
            'documents_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'doctor_name', 'specialty', 'created_at', 'updated_at']

    def get_documents_count(self, obj):
        """Count documents attached to this appointment."""
        return obj.documents.filter(deleted_at__isnull=True).count()


class MedicalDocumentSerializer(serializers.ModelSerializer):
    """Serializer for medical documents."""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)

    class Meta:
        model = MedicalDocument
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'appointment',
            'title',
            'document_type',
            'document_type_display',
            'document_date',
            'file',
            'file_url',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Ensure at least file or file_url is provided."""
        file = data.get('file')
        file_url = data.get('file_url')
        
        if not file and not file_url:
            raise serializers.ValidationError(
                "Please provide either a file upload or a file URL."
            )
        
        return data


class AppointmentStatsSerializer(serializers.Serializer):
    """Statistics for appointments dashboard."""
    upcoming_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    missed_count = serializers.IntegerField()
    next_appointment = AppointmentListSerializer(allow_null=True)
    recent_appointments = AppointmentListSerializer(many=True)
