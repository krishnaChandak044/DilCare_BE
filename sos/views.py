"""
SOS — API views for emergency contacts and SOS triggering.
"""
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from core.mixins import OwnerQuerySetMixin
from core.permissions import IsOwner
from accounts.services import NotificationService
from .models import EmergencyContact, SOSAlert
from .serializers import (
    EmergencyContactSerializer,
    CreateEmergencyContactSerializer,
    SOSAlertSerializer,
    TriggerSOSSerializer,
)


# ============ Emergency Contacts ============

class EmergencyContactListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/sos/contacts/      — list all emergency contacts
    POST /api/v1/sos/contacts/      — add a new emergency contact
    """
    queryset = EmergencyContact.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateEmergencyContactSerializer
        return EmergencyContactSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmergencyContactDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/sos/contacts/{id}/  — retrieve a contact
    PATCH  /api/v1/sos/contacts/{id}/  — update a contact
    DELETE /api/v1/sos/contacts/{id}/  — soft-delete a contact
    """
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated, IsOwner]


# ============ SOS Trigger ============

class TriggerSOSView(APIView):
    """
    POST /api/v1/sos/trigger/  — trigger an SOS alert.
    Logs the alert, attaches all user contacts, returns alert details.
    Sends push notifications to family members.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=TriggerSOSSerializer, responses={201: SOSAlertSerializer})
    def post(self, request):
        ser = TriggerSOSSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        alert = SOSAlert.objects.create(
            user=request.user,
            latitude=ser.validated_data.get("latitude"),
            longitude=ser.validated_data.get("longitude"),
        )
        # attach all user's contacts to the alert
        contacts = EmergencyContact.objects.filter(user=request.user)
        alert.notified_contacts.set(contacts)

        # Send push notifications to family members
        try:
            from family.models import FamilyMember
            family_members = FamilyMember.objects.filter(
                parent_user=request.user
            ).select_related('family_member_user')
            
            if family_members.exists():
                recipients = [fm.family_member_user for fm in family_members]
                location_address = ser.validated_data.get("location_address", "Unknown location")
                
                # Send notifications
                NotificationService.send_to_users(
                    users=recipients,
                    title=f"🚨 SOS Alert: {request.user.get_full_name()} needs help!",
                    body=f"Location: {location_address}. Respond immediately.",
                    notification_type="sos_alert",
                    action="sos_alert",
                    data={
                        "sos_alert_id": str(alert.id),
                        "location_lat": str(alert.latitude),
                        "location_lng": str(alert.longitude),
                    }
                )
        except Exception as e:
            # Log error but don't fail the SOS creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending SOS notifications: {str(e)}")

        return Response(
            SOSAlertSerializer(alert).data,
            status=status.HTTP_201_CREATED,
        )


class SOSAlertListView(OwnerQuerySetMixin, generics.ListAPIView):
    """
    GET /api/v1/sos/alerts/  — list all SOS alerts for the user (history).
    """
    queryset = SOSAlert.objects.all()
    serializer_class = SOSAlertSerializer
    permission_classes = [IsAuthenticated]


class SOSAlertResolveView(APIView):
    """
    POST /api/v1/sos/alerts/{id}/resolve/  — mark an alert as resolved.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: SOSAlertSerializer})
    def post(self, request, pk):
        try:
            alert = SOSAlert.objects.get(pk=pk, user=request.user)
        except SOSAlert.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        alert.resolved = True
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["resolved", "resolved_at"])
        return Response(SOSAlertSerializer(alert).data)

