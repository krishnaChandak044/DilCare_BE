"""
Medicine — API views for medicine and prescription management.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.mixins import OwnerQuerySetMixin
from core.permissions import IsOwner
from .models import Medicine, MedicineIntake, Prescription
from .serializers import (
    MedicineSerializer,
    MedicineIntakeSerializer,
    MedicineIntakeToggleSerializer,
    PrescriptionSerializer,
    TodayMedicineSerializer,
    MedicineSummarySerializer,
)


# Medicine Views 

class MedicineListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET: List all medicines for the authenticated user.
    POST: Create a new medicine.
    """
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]
    owner_field = "user"

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        
        return qs

    def perform_create(self, serializer):
        medicine = serializer.save(user=self.request.user)
        # Auto-generate today's intakes
        self._generate_intakes_for_date(medicine, timezone.localdate())

    def _generate_intakes_for_date(self, medicine, date):
        """Generate intake records for a medicine on a given date."""
        from datetime import datetime
        
        for time_str in medicine.time_list:
            try:
                scheduled_time = datetime.strptime(time_str, "%H:%M").time()
                MedicineIntake.objects.get_or_create(
                    medicine=medicine,
                    scheduled_date=date,
                    scheduled_time=scheduled_time,
                    defaults={"status": "pending"}
                )
            except ValueError:
                continue


class MedicineDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a medicine.
    PUT/PATCH: Update a medicine.
    DELETE: Soft-delete a medicine.
    """
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"

    def perform_destroy(self, instance):
        instance.soft_delete()


# ============ Medicine Intake Views ============

class TodayMedicinesView(APIView):
    """
    GET: Get today's medicine schedule with intake status.
    Returns a flat list of medicines with their scheduled times and status.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: TodayMedicineSerializer(many=True)},
        parameters=[
            OpenApiParameter(name="date", type=str, description="Date in YYYY-MM-DD format (default: today)")
        ]
    )
    def get(self, request):
        date_str = request.query_params.get("date")
        if date_str:
            try:
                from datetime import datetime
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.localdate()

        medicines = Medicine.objects.filter(user=request.user, is_active=True)
        result = []

        for medicine in medicines:
            for time_str in medicine.time_list:
                try:
                    from datetime import datetime
                    scheduled_time = datetime.strptime(time_str, "%H:%M").time()
                except ValueError:
                    continue

                # Get or create intake for this medicine/date/time
                intake, created = MedicineIntake.objects.get_or_create(
                    medicine=medicine,
                    scheduled_date=target_date,
                    scheduled_time=scheduled_time,
                    defaults={"status": "pending"}
                )

                result.append({
                    "id": medicine.id,
                    "name": medicine.name,
                    "dosage": medicine.dosage,
                    "frequency": medicine.get_frequency_display(),
                    "time": time_str,
                    "taken": intake.status == "taken",
                    "missed": intake.status == "missed",
                    "intake_id": intake.id,
                })

        # Sort by time
        result.sort(key=lambda x: x["time"])
        
        return Response(result)


class MedicineIntakeToggleView(APIView):
    """
    POST: Toggle or set the intake status for a medicine.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=MedicineIntakeToggleSerializer,
        responses={200: MedicineIntakeSerializer}
    )
    def post(self, request, intake_id):
        try:
            intake = MedicineIntake.objects.select_related("medicine").get(
                id=intake_id,
                medicine__user=request.user
            )
        except MedicineIntake.DoesNotExist:
            return Response(
                {"error": "Intake not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MedicineIntakeToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")
        notes = serializer.validated_data.get("notes", "")

        if new_status:
            intake.status = new_status
        else:
            # Toggle between taken and pending
            intake.status = "pending" if intake.status == "taken" else "taken"

        if intake.status == "taken":
            intake.taken_at = timezone.now()
        else:
            intake.taken_at = None

        if notes:
            intake.notes = notes

        intake.save()

        return Response(MedicineIntakeSerializer(intake).data)


class MedicineIntakeListView(OwnerQuerySetMixin, generics.ListAPIView):
    """
    GET: List medicine intakes for the authenticated user.
    Filters: date, medicine_id, status
    """
    queryset = MedicineIntake.objects.all()
    serializer_class = MedicineIntakeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = MedicineIntake.objects.filter(
            medicine__user=self.request.user
        ).select_related("medicine")

        # Filter by date
        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                from datetime import datetime
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                qs = qs.filter(scheduled_date=target_date)
            except ValueError:
                pass

        # Filter by medicine
        medicine_id = self.request.query_params.get("medicine_id")
        if medicine_id:
            qs = qs.filter(medicine_id=medicine_id)

        # Filter by status
        intake_status = self.request.query_params.get("status")
        if intake_status:
            qs = qs.filter(status=intake_status)

        return qs


# ============ Medicine Summary View ============

class MedicineSummaryView(APIView):
    """
    GET: Get medicine adherence summary and statistics.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MedicineSummarySerializer})
    def get(self, request):
        today = timezone.localdate()
        
        # Medicine counts
        medicines = Medicine.objects.filter(user=request.user)
        total_medicines = medicines.count()
        active_medicines = medicines.filter(is_active=True).count()

        # Today's stats
        today_intakes = MedicineIntake.objects.filter(
            medicine__user=request.user,
            scheduled_date=today
        )
        today_total = today_intakes.count()
        today_taken = today_intakes.filter(status="taken").count()
        today_missed = today_intakes.filter(status="missed").count()
        today_pending = today_intakes.filter(status="pending").count()

        # 7-day adherence rate
        week_ago = today - timedelta(days=7)
        week_intakes = MedicineIntake.objects.filter(
            medicine__user=request.user,
            scheduled_date__gte=week_ago,
            scheduled_date__lt=today
        )
        week_total = week_intakes.count()
        week_taken = week_intakes.filter(status="taken").count()
        adherence_7d = (week_taken / week_total * 100) if week_total > 0 else 0.0

        # 30-day adherence rate
        month_ago = today - timedelta(days=30)
        month_intakes = MedicineIntake.objects.filter(
            medicine__user=request.user,
            scheduled_date__gte=month_ago,
            scheduled_date__lt=today
        )
        month_total = month_intakes.count()
        month_taken = month_intakes.filter(status="taken").count()
        adherence_30d = (month_taken / month_total * 100) if month_total > 0 else 0.0

        data = {
            "total_medicines": total_medicines,
            "active_medicines": active_medicines,
            "today_total": today_total,
            "today_taken": today_taken,
            "today_missed": today_missed,
            "today_pending": today_pending,
            "adherence_rate_7d": round(adherence_7d, 1),
            "adherence_rate_30d": round(adherence_30d, 1),
        }

        return Response(data)


# ============ Prescription Views ============

class PrescriptionListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET: List all prescriptions for the authenticated user.
    POST: Upload a new prescription.
    """
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    owner_field = "user"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PrescriptionDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a prescription.
    PUT/PATCH: Update a prescription.
    DELETE: Soft-delete a prescription.
    """
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"

    def perform_destroy(self, instance):
        instance.soft_delete()
