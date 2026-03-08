"""
Doctor — API views for managing doctors, appointments, and documents.
"""
from django.utils import timezone
from django.db.models import Q, Count
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from core.mixins import OwnerQuerySetMixin
from core.permissions import IsOwner
from .models import Doctor, Appointment, MedicalDocument
from .serializers import (
    DoctorSerializer,
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    MedicalDocumentSerializer,
    AppointmentStatsSerializer,
)


# ══════════════════════════════════════════════════════════════
# DOCTOR VIEWS
# ══════════════════════════════════════════════════════════════

class DoctorListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET: List all doctors for current user
    POST: Add a new doctor
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    owner_field = 'user'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DoctorDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve doctor details
    PUT/PATCH: Update doctor
    DELETE: Soft delete doctor
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = 'user'

    def perform_destroy(self, instance):
        instance.soft_delete()


# ══════════════════════════════════════════════════════════════
# APPOINTMENT VIEWS
# ══════════════════════════════════════════════════════════════

class AppointmentListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET: List appointments (with optional filters)
    POST: Create new appointment
    """
    queryset = Appointment.objects.select_related('doctor')
    permission_classes = [IsAuthenticated]
    owner_field = 'user'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AppointmentDetailSerializer
        return AppointmentListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter upcoming vs past
        time_filter = self.request.query_params.get('time')
        today = timezone.now().date()
        if time_filter == 'upcoming':
            queryset = queryset.filter(
                appointment_date__gte=today
            ).filter(Q(status='scheduled') | Q(status='completed'))
        elif time_filter == 'past':
            queryset = queryset.filter(appointment_date__lt=today)
        
        # Filter by doctor
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AppointmentDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve appointment details
    PUT/PATCH: Update appointment
    DELETE: Soft delete appointment
    """
    queryset = Appointment.objects.select_related('doctor')
    serializer_class = AppointmentDetailSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = 'user'

    def perform_destroy(self, instance):
        instance.soft_delete()


class AppointmentStatsView(APIView):
    """
    GET: Get appointment statistics and upcoming appointments.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AppointmentStatsSerializer})
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Get counts by status
        appointments = Appointment.objects.filter(
            user=user,
            deleted_at__isnull=True
        )
        
        upcoming_count = appointments.filter(
            appointment_date__gte=today,
            status='scheduled'
        ).count()
        
        completed_count = appointments.filter(status='completed').count()
        cancelled_count = appointments.filter(status='cancelled').count()
        missed_count = appointments.filter(status='missed').count()
        
        # Next appointment
        next_appointment = appointments.filter(
            appointment_date__gte=today,
            status='scheduled'
        ).select_related('doctor').order_by('appointment_date', 'appointment_time').first()
        
        # Recent appointments (last 5)
        recent_appointments = appointments.order_by(
            '-appointment_date', '-appointment_time'
        ).select_related('doctor')[:5]
        
        data = {
            'upcoming_count': upcoming_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
            'missed_count': missed_count,
            'next_appointment': AppointmentListSerializer(next_appointment).data if next_appointment else None,
            'recent_appointments': AppointmentListSerializer(recent_appointments, many=True).data,
        }
        
        return Response(data)


# ══════════════════════════════════════════════════════════════
# MEDICAL DOCUMENTS VIEWS
# ══════════════════════════════════════════════════════════════

class MedicalDocumentListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET: List all medical documents
    POST: Upload a new document
    """
    queryset = MedicalDocument.objects.select_related('doctor', 'appointment')
    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    owner_field = 'user'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by document type
        doc_type = self.request.query_params.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        # Filter by doctor
        doctor_id = self.request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        # Filter by appointment
        appointment_id = self.request.query_params.get('appointment')
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MedicalDocumentDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve document details
    PUT/PATCH: Update document
    DELETE: Soft delete document
    """
    queryset = MedicalDocument.objects.select_related('doctor', 'appointment')
    serializer_class = MedicalDocumentSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    parser_classes = [MultiPartParser, FormParser]
    owner_field = 'user'

    def perform_destroy(self, instance):
        instance.soft_delete()

