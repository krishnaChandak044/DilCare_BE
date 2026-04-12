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
    MedicineInventoryUpdateSerializer,
    MedicineIntakeSerializer,
    MedicineIntakeToggleSerializer,
    PrescriptionSerializer,
    TodayMedicineSerializer,
    MedicineSummarySerializer,
)


# ============ Medicine Views ============

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
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    def perform_create(self, serializer):
        # Auto-set doses_per_day from schedule_times count
        schedule_times = serializer.validated_data.get("schedule_times", "08:00")
        doses = max(1, len([t.strip() for t in schedule_times.split(",") if t.strip()]))
        # Only override if not explicitly provided
        if "doses_per_day" not in serializer.validated_data:
            serializer.validated_data["doses_per_day"] = doses
        medicine = serializer.save(user=self.request.user)
        self._generate_intakes_for_date(medicine, timezone.localdate())
        
        # Trigger family notification that a new medicine was added
        _notify_family_new_medicine(self.request.user, medicine)

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


class MedicineInventoryUpdateView(OwnerQuerySetMixin, generics.UpdateAPIView):
    """
    PATCH /medicine/medicines/<id>/inventory/
    Update the current_quantity and/or doses_per_day of a medicine.
    Also triggers family notification if medicine is running low after update.
    """
    queryset = Medicine.objects.all()
    serializer_class = MedicineInventoryUpdateSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        serializer.save()

    def patch(self, request, *args, **kwargs):
        response = self.partial_update(request, *args, **kwargs)
        # After update, check if running low and send family notification
        instance = self.get_object()
        if instance.is_running_low:
            _notify_family_medicine_low(request.user, instance)
        return response


# ============ Medicine Intake Views ============

class TodayMedicinesView(APIView):
    """
    GET: Get today's medicine schedule with intake status + inventory info.
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
                from datetime import datetime as dt
                target_date = dt.strptime(date_str, "%Y-%m-%d").date()
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
                    from datetime import datetime as dt
                    scheduled_time = dt.strptime(time_str, "%H:%M").time()
                except ValueError:
                    continue

                intake, _ = MedicineIntake.objects.get_or_create(
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
                    # Inventory
                    "current_quantity": medicine.current_quantity,
                    "doses_per_day": medicine.doses_per_day,
                    "inventory_end_date": medicine.inventory_end_date,
                    "days_until_empty": medicine.days_until_empty,
                    "is_running_low": medicine.is_running_low,
                })

        result.sort(key=lambda x: x["time"])
        return Response(result)


class RunningOutMedicinesView(APIView):
    """
    GET /medicine/running-out/
    Returns medicines that will run out within 2 days.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        medicines = Medicine.objects.filter(
            user=request.user,
            is_active=True,
            current_quantity__isnull=False,
        )
        running_low = [m for m in medicines if m.is_running_low]
        data = []
        for m in running_low:
            data.append({
                "id": str(m.id),
                "name": m.name,
                "dosage": m.dosage,
                "current_quantity": m.current_quantity,
                "doses_per_day": m.doses_per_day,
                "days_until_empty": m.days_until_empty,
                "inventory_end_date": m.inventory_end_date.isoformat() if m.inventory_end_date else None,
            })
        return Response({"running_low": data, "count": len(data)})


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
            intake.status = "pending" if intake.status == "taken" else "taken"

        if intake.status == "taken":
            intake.taken_at = timezone.now()
            # Decrement inventory if quantity is tracked
            medicine = intake.medicine
            if medicine.current_quantity is not None and medicine.current_quantity > 0:
                medicine.current_quantity -= 1
                medicine.save(update_fields=["current_quantity"])
                # Check if now running low
                if medicine.is_running_low:
                    _notify_family_medicine_low(request.user, medicine)
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

        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                from datetime import datetime as dt
                target_date = dt.strptime(date_str, "%Y-%m-%d").date()
                qs = qs.filter(scheduled_date=target_date)
            except ValueError:
                pass

        medicine_id = self.request.query_params.get("medicine_id")
        if medicine_id:
            qs = qs.filter(medicine_id=medicine_id)

        intake_status = self.request.query_params.get("status")
        if intake_status:
            qs = qs.filter(status=intake_status)

        return qs


# ============ Medicine Summary View ============

class MedicineSummaryView(APIView):
    """
    GET: Get medicine adherence summary and statistics (including inventory).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MedicineSummarySerializer})
    def get(self, request):
        today = timezone.localdate()

        medicines = Medicine.objects.filter(user=request.user)
        total_medicines = medicines.count()
        active_medicines = medicines.filter(is_active=True).count()

        today_intakes = MedicineIntake.objects.filter(
            medicine__user=request.user,
            scheduled_date=today
        )
        today_total = today_intakes.count()
        today_taken = today_intakes.filter(status="taken").count()
        today_missed = today_intakes.filter(status="missed").count()
        today_pending = today_intakes.filter(status="pending").count()

        week_ago = today - timedelta(days=7)
        week_intakes = MedicineIntake.objects.filter(
            medicine__user=request.user,
            scheduled_date__gte=week_ago,
            scheduled_date__lt=today
        )
        week_total = week_intakes.count()
        week_taken = week_intakes.filter(status="taken").count()
        adherence_7d = (week_taken / week_total * 100) if week_total > 0 else 0.0

        month_ago = today - timedelta(days=30)
        month_intakes = MedicineIntake.objects.filter(
            medicine__user=request.user,
            scheduled_date__gte=month_ago,
            scheduled_date__lt=today
        )
        month_total = month_intakes.count()
        month_taken = month_intakes.filter(status="taken").count()
        adherence_30d = (month_taken / month_total * 100) if month_total > 0 else 0.0

        # Inventory summary
        active_meds = medicines.filter(is_active=True, current_quantity__isnull=False)
        running_low_count = sum(1 for m in active_meds if m.is_running_low)

        data = {
            "total_medicines": total_medicines,
            "active_medicines": active_medicines,
            "today_total": today_total,
            "today_taken": today_taken,
            "today_missed": today_missed,
            "today_pending": today_pending,
            "adherence_rate_7d": round(adherence_7d, 1),
            "adherence_rate_30d": round(adherence_30d, 1),
            "running_low_count": running_low_count,
        }

        return Response(data)


# ============ Prescription Views ============

class PrescriptionListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    owner_field = "user"

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PrescriptionDetailView(OwnerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"

    def perform_destroy(self, instance):
        instance.soft_delete()


# ============ Internal Helper ============

def _notify_family_new_medicine(user, medicine):
    """
    Create in-app Notification records for all family members of `user`
    telling them that a new medicine was added.
    """
    try:
        from accounts.models import Notification
        from family.models import FamilyMembership

        # Get this user's family
        try:
            membership = FamilyMembership.objects.select_related("family").get(user=user)
        except FamilyMembership.DoesNotExist:
            return

        family = membership.family
        # All other members in the family
        other_memberships = FamilyMembership.objects.filter(
            family=family
        ).exclude(user=user).select_related("user")

        for m in other_memberships:
            Notification.objects.create(
                user=m.user,
                title="New Medicine Added",
                body=f"{user.get_full_name() or user.username} has added a new medicine: {medicine.name}.",
                notification_type="medication_reminder",
                action="open_medicine",
                data={"medicine_id": str(medicine.id), "user_id": str(user.id)}
            )
            # Todo: trigger Expo Push Notification here if FCM setup
    except Exception as e:
        print(f"Error sending new medicine notification: {e}")

def _notify_family_medicine_low(user, medicine):
    """
    Create in-app Notification records for all family members of `user`
    telling them that the medicine is running low.
    Falls back silently if the user has no family.
    """
    try:
        from accounts.models import Notification
        from family.models import FamilyMembership

        # Get this user's family
        try:
            membership = FamilyMembership.objects.select_related("family").get(user=user)
        except FamilyMembership.DoesNotExist:
            return

        family = membership.family
        # All other members in the family
        other_memberships = FamilyMembership.objects.filter(
            family=family
        ).exclude(user=user).select_related("user")

        user_name = user.get_full_name() or user.email.split("@")[0]
        days = medicine.days_until_empty
        qty = medicine.current_quantity
        end_str = medicine.inventory_end_date.strftime("%d %b") if medicine.inventory_end_date else "soon"

        title = f"💊 {user_name}'s {medicine.name} is running out!"
        body = (
            f"{user_name} has only {qty} tablet(s) of {medicine.name} left. "
            f"It will run out by {end_str} ({days} day(s) left). "
            f"Please get a refill or revisit the doctor."
        )

        notifications = []
        for m in other_memberships:
            notifications.append(Notification(
                user=m.user,
                title=title,
                body=body,
                notification_type="medication_reminder",
                action="Medicine",
                data={
                    "medicine_id": str(medicine.id),
                    "medicine_name": medicine.name,
                    "days_until_empty": days,
                    "current_quantity": qty,
                },
            ))
        if notifications:
            Notification.objects.bulk_create(notifications)
    except Exception:
        # Never crash the main flow due to notification failure
        pass
