"""
SOS — URL configuration.
"""
from django.urls import path
from .views import (
    EmergencyContactListCreateView,
    EmergencyContactDetailView,
    TriggerSOSView,
    SOSAlertListView,
    SOSAlertResolveView,
)

urlpatterns = [
    path("contacts/", EmergencyContactListCreateView.as_view(), name="sos-contacts-list-create"),
    path("contacts/<uuid:pk>/", EmergencyContactDetailView.as_view(), name="sos-contact-detail"),
    path("trigger/", TriggerSOSView.as_view(), name="sos-trigger"),
    path("alerts/", SOSAlertListView.as_view(), name="sos-alerts-list"),
    path("alerts/<uuid:pk>/resolve/", SOSAlertResolveView.as_view(), name="sos-alert-resolve"),
]
