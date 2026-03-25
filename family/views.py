"""
Family — API views for family linking functionality.
Enables children to link to and monitor parents' health.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from drf_spectacular.utils import extend_schema

from .models import FamilyLink
from .serializers import (
    FamilyLinkSerializer,
    LinkParentSerializer,
    ParentHealthSummarySerializer,
)

User = get_user_model()


class LinkedParentsListView(generics.ListAPIView):
    """
    GET: List all parents linked to the current user (child).
    """
    serializer_class = FamilyLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FamilyLink.objects.filter(
            child=self.request.user,
            is_active=True
        ).select_related("parent")


class LinkParentView(APIView):
    """
    POST: Link to a parent using their unique link code.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "link_parent"

    @extend_schema(request=LinkParentSerializer, responses={201: FamilyLinkSerializer})
    def post(self, request):
        serializer = LinkParentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        link_code = serializer.validated_data["link_code"].upper()
        relationship = serializer.validated_data.get("relationship", "other")

        # Find the parent by link code
        try:
            parent = User.objects.get(parent_link_code=link_code)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid link code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent self-linking
        if parent == request.user:
            return Response(
                {"error": "You cannot link to yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already linked
        existing = FamilyLink.objects.filter(
            child=request.user,
            parent=parent
        ).first()

        if existing:
            if existing.is_active:
                return Response(
                    {"error": "You are already linked to this parent."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Reactivate existing link
                existing.is_active = True
                existing.relationship = relationship
                existing.save()
                return Response(
                    FamilyLinkSerializer(existing).data,
                    status=status.HTTP_200_OK
                )

        # Create new link
        link = FamilyLink.objects.create(
            child=request.user,
            parent=parent,
            relationship=relationship,
            is_active=True,
        )

        return Response(
            FamilyLinkSerializer(link).data,
            status=status.HTTP_201_CREATED
        )


class UnlinkParentView(APIView):
    """
    POST: Unlink from a parent (deactivate the link).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, parent_id):
        try:
            link = FamilyLink.objects.get(
                child=request.user,
                parent_id=parent_id,
                is_active=True
            )
        except FamilyLink.DoesNotExist:
            return Response(
                {"error": "Link not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        link.is_active = False
        link.save()

        return Response({"message": "Successfully unlinked."})


class ParentHealthView(APIView):
    """
    GET: Get health summary for a linked parent.
    Returns aggregated health data the child is allowed to see.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ParentHealthSummarySerializer})
    def get(self, request, parent_id):
        # Verify link exists and is active
        try:
            link = FamilyLink.objects.select_related("parent").get(
                child=request.user,
                parent_id=parent_id,
                is_active=True
            )
        except FamilyLink.DoesNotExist:
            return Response(
                {"error": "You are not linked to this parent."},
                status=status.HTTP_403_FORBIDDEN
            )

        parent = link.parent
        today = timezone.localdate()

        # Get latest health readings
        latest_bp = None
        bp_status = None
        bp_recorded_at = None
        latest_sugar = None
        sugar_status = None
        sugar_recorded_at = None
        latest_heart_rate = None
        heart_rate_status = None
        heart_rate_recorded_at = None

        # Try to get health readings if health app exists
        try:
            from health.models import HealthReading

            bp_reading = HealthReading.objects.filter(
                user=parent, reading_type="bp"
            ).order_by("-recorded_at").first()
            if bp_reading:
                latest_bp = bp_reading.value
                bp_status = bp_reading.status
                bp_recorded_at = bp_reading.recorded_at

            sugar_reading = HealthReading.objects.filter(
                user=parent, reading_type="sugar"
            ).order_by("-recorded_at").first()
            if sugar_reading:
                latest_sugar = sugar_reading.value
                sugar_status = sugar_reading.status
                sugar_recorded_at = sugar_reading.recorded_at

            hr_reading = HealthReading.objects.filter(
                user=parent, reading_type="heartRate"
            ).order_by("-recorded_at").first()
            if hr_reading:
                try:
                    latest_heart_rate = int(float(hr_reading.value))
                except (ValueError, TypeError):
                    latest_heart_rate = None
                heart_rate_status = hr_reading.status
                heart_rate_recorded_at = hr_reading.recorded_at
        except ImportError:
            pass

        # Get medicine adherence
        medicines_today_total = 0
        medicines_today_taken = 0
        medicine_adherence_percent = 0.0

        try:
            from medicine.models import MedicineIntake

            today_intakes = MedicineIntake.objects.filter(
                medicine__user=parent,
                scheduled_date=today
            )
            medicines_today_total = today_intakes.count()
            medicines_today_taken = today_intakes.filter(status="taken").count()
            if medicines_today_total > 0:
                medicine_adherence_percent = round(
                    (medicines_today_taken / medicines_today_total) * 100, 1
                )
        except ImportError:
            pass

        # Get water intake
        water_glasses_today = 0
        water_goal_today = 8

        try:
            from water.models import DailyWaterLog

            water_log = DailyWaterLog.objects.filter(
                user=parent,
                date=today
            ).first()
            if water_log:
                water_glasses_today = water_log.glasses
                water_goal_today = water_log.goal_glasses
        except ImportError:
            pass

        # Determine overall status
        danger_indicators = [bp_status, sugar_status, heart_rate_status]
        if "danger" in danger_indicators:
            overall_status = "danger"
        elif "warning" in danger_indicators:
            overall_status = "warning"
        else:
            overall_status = "good"

        # Find last activity
        last_activity = None
        activity_times = [t for t in [bp_recorded_at, sugar_recorded_at, heart_rate_recorded_at] if t]
        if activity_times:
            last_activity = max(activity_times)

        data = {
            "parent_id": parent.id,
            "parent_name": parent.get_full_name() or parent.email,
            "relationship": link.get_relationship_display(),
            "latest_bp": latest_bp,
            "bp_status": bp_status,
            "bp_recorded_at": bp_recorded_at,
            "latest_sugar": latest_sugar,
            "sugar_status": sugar_status,
            "sugar_recorded_at": sugar_recorded_at,
            "latest_heart_rate": latest_heart_rate,
            "heart_rate_status": heart_rate_status,
            "heart_rate_recorded_at": heart_rate_recorded_at,
            "medicines_today_total": medicines_today_total,
            "medicines_today_taken": medicines_today_taken,
            "medicine_adherence_percent": medicine_adherence_percent,
            "water_glasses_today": water_glasses_today,
            "water_goal_today": water_goal_today,
            "overall_status": overall_status,
            "last_activity": last_activity,
        }

        return Response(data)


class MyLinkCodeView(APIView):
    """
    GET: Get current user's link code (for sharing with children).
    POST: Regenerate link code.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "link_code_regenerate"

    def get(self, request):
        return Response({
            "link_code": request.user.parent_link_code,
            "linked_children_count": FamilyLink.objects.filter(
                parent=request.user,
                is_active=True
            ).count(),
        })

    def post(self, request):
        new_code = request.user.regenerate_link_code()
        return Response({
            "link_code": new_code,
            "message": "Link code regenerated successfully.",
        })
