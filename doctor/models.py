"""
Doctor — Models for managing doctors, appointments, and medical documents.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from core.models import SoftDeleteModel

User = get_user_model()


class Doctor(SoftDeleteModel):
    """
    Doctor profile - stores details about healthcare providers.
    Each user can have multiple doctors.
    """
    SPECIALTY_CHOICES = [
        ('general', 'General Physician'),
        ('cardiologist', 'Cardiologist'),
        ('diabetologist', 'Diabetologist'),
        ('neurologist', 'Neurologist'),
        ('orthopedic', 'Orthopedic'),
        ('dermatologist', 'Dermatologist'),
        ('gynecologist', 'Gynecologist'),
        ('pediatrician', 'Pediatrician'),
        ('psychiatrist', 'Psychiatrist'),
        ('ophthalmologist', 'Ophthalmologist'),
        ('ent', 'ENT Specialist'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=50, choices=SPECIALTY_CHOICES, default='general')
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(blank=True)
    
    hospital = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Personal notes about this doctor")
    
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as primary care physician"
    )

    class Meta:
        ordering = ['-is_primary', 'name']
        indexes = [
            models.Index(fields=['user', '-is_primary']),
            models.Index(fields=['user', 'specialty']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_specialty_display()})"


class Appointment(SoftDeleteModel):
    """
    Medical appointments - past and upcoming.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )
    
    doctor_name = models.CharField(
        max_length=200,
        help_text="Stored in case doctor is deleted"
    )
    specialty = models.CharField(max_length=50, blank=True)
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField(null=True, blank=True)
    
    reason = models.TextField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, help_text="Post-appointment notes")
    
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['user', '-appointment_date']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.doctor_name} - {self.appointment_date}"

    def save(self, *args, **kwargs):
        # Auto-populate doctor_name from doctor if available
        if self.doctor and not self.doctor_name:
            self.doctor_name = self.doctor.name
        if self.doctor and not self.specialty:
            self.specialty = self.doctor.get_specialty_display()
        super().save(*args, **kwargs)


class MedicalDocument(SoftDeleteModel):
    """
    Store medical documents, prescriptions, lab reports, etc.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('prescription', 'Prescription'),
        ('lab_report', 'Lab Report'),
        ('scan', 'Medical Scan'),
        ('xray', 'X-Ray'),
        ('discharge_summary', 'Discharge Summary'),
        ('insurance', 'Insurance Document'),
        ('vaccination', 'Vaccination Record'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_documents')
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, default='other')
    document_date = models.DateField(help_text="Date of the document/report")
    
    file = models.FileField(upload_to='medical_documents/%Y/%m/', blank=True)
    file_url = models.URLField(blank=True, help_text="External URL if not uploaded")
    
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-document_date']
        indexes = [
            models.Index(fields=['user', '-document_date']),
            models.Index(fields=['user', 'document_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.document_date})"
