"""
Doctor — URL routes for doctor management endpoints.
"""
from django.urls import path
from .views import (
    DoctorListCreateView,
    DoctorDetailView,
    AppointmentListCreateView,
    AppointmentDetailView,
    AppointmentStatsView,
    MedicalDocumentListCreateView,
    MedicalDocumentDetailView,
)

app_name = "doctor"

urlpatterns = [
    # Doctors
    path("doctors/", DoctorListCreateView.as_view(), name="doctor-list"),
    path("doctors/<uuid:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
    
    # Appointments
    path("appointments/", AppointmentListCreateView.as_view(), name="appointment-list"),
    path("appointments/stats/", AppointmentStatsView.as_view(), name="appointment-stats"),
    path("appointments/<uuid:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    
    # Medical Documents
    path("documents/", MedicalDocumentListCreateView.as_view(), name="document-list"),
    path("documents/<uuid:pk>/", MedicalDocumentDetailView.as_view(), name="document-detail"),
]
