"""
Family — API views for family group functionality.
Create, join, view, and manage a family group of up to 5 members.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import Family, FamilyMembership
from .serializers import (
    CreateFamilySerializer,
    JoinFamilySerializer,
    FamilySerializer,
    FamilyMemberHealthSummarySerializer,
    UpgradePlanSerializer,
)

User = get_user_model()


def _get_member_health_data(member_user):
    """
    Build health summary dict for a given user.
    Shared helper used by FamilyMemberHealthView.
    """
    today = timezone.localdate()

    # ── Health readings ──────────────────────────────────────
    latest_bp = bp_status = bp_recorded_at = None
    latest_sugar = sugar_status = sugar_recorded_at = None
    latest_heart_rate = heart_rate_status = heart_rate_recorded_at = None

    try:
        from health.models import HealthReading

        bp = HealthReading.objects.filter(
            user=member_user, reading_type="bp"
        ).order_by("-recorded_at").first()
        if bp:
            latest_bp = bp.value
            bp_status = bp.status
            bp_recorded_at = bp.recorded_at

        sugar = HealthReading.objects.filter(
            user=member_user, reading_type="sugar"
        ).order_by("-recorded_at").first()
        if sugar:
            latest_sugar = sugar.value
            sugar_status = sugar.status
            sugar_recorded_at = sugar.recorded_at

        hr = HealthReading.objects.filter(
            user=member_user, reading_type="heartRate"
        ).order_by("-recorded_at").first()
        if hr:
            try:
                latest_heart_rate = int(float(hr.value))
            except (ValueError, TypeError):
                latest_heart_rate = None
            heart_rate_status = hr.status
            heart_rate_recorded_at = hr.recorded_at
    except ImportError:
        pass

    # ── Medicine adherence ───────────────────────────────────
    medicines_today_total = medicines_today_taken = 0
    medicine_adherence_percent = 0.0

    try:
        from medicine.models import MedicineIntake
        intakes = MedicineIntake.objects.filter(
            medicine__user=member_user, scheduled_date=today
        )
        medicines_today_total = intakes.count()
        medicines_today_taken = intakes.filter(status="taken").count()
        if medicines_today_total > 0:
            medicine_adherence_percent = round(
                (medicines_today_taken / medicines_today_total) * 100, 1
            )
    except ImportError:
        pass

    # ── Water intake ─────────────────────────────────────────
    water_glasses_today = 0
    water_goal_today = 8

    try:
        from water.models import DailyWaterLog
        wlog = DailyWaterLog.objects.filter(
            user=member_user, date=today
        ).first()
        if wlog:
            water_glasses_today = wlog.glasses
            water_goal_today = wlog.goal_glasses
    except ImportError:
        pass

    # ── Overall status ───────────────────────────────────────
    indicators = [bp_status, sugar_status, heart_rate_status]
    if "danger" in indicators:
        overall_status = "danger"
    elif "warning" in indicators:
        overall_status = "warning"
    else:
        overall_status = "good"

    activity_times = [t for t in [bp_recorded_at, sugar_recorded_at, heart_rate_recorded_at] if t]
    last_activity = max(activity_times) if activity_times else None

    return {
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


# ─────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────

class CreateFamilyView(APIView):
    """
    POST /api/v1/family/create/
    Create a new family group. The creator becomes admin.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=CreateFamilySerializer, responses={201: FamilySerializer})
    def post(self, request):
        # Check if user already belongs to a family
        if FamilyMembership.objects.filter(user=request.user).exists():
            return Response(
                {"error": "You already belong to a family. Leave it first to create a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateFamilySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        family = Family.objects.create(
            name=serializer.validated_data["name"],
            created_by=request.user,
        )
        FamilyMembership.objects.create(
            family=family,
            user=request.user,
            role="admin",
        )

        return Response(
            FamilySerializer(family).data,
            status=status.HTTP_201_CREATED,
        )


class JoinFamilyView(APIView):
    """
    POST /api/v1/family/join/
    Join a family using the family's invite code or any member's personal link code (parent_link_code).
    If you are the only member of your current family, that empty group is dissolved so you can join.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=JoinFamilySerializer, responses={200: FamilySerializer})
    def post(self, request):
        existing = FamilyMembership.objects.select_related("family").filter(user=request.user).first()
        if existing:
            if existing.family.memberships.count() == 1:
                fam = existing.family
                existing.delete()
                fam.delete()
            else:
                return Response(
                    {"error": "You already belong to a family. Leave it first to join another."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = JoinFamilySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        family = serializer.validated_data["resolved_family"]
        nickname = serializer.validated_data.get("nickname", "")

        if family.is_full:
            return Response(
                {"error": f"This family already has {family.max_members} members (maximum)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        FamilyMembership.objects.create(
            family=family,
            user=request.user,
            role="member",
            nickname=nickname,
        )

        return Response(FamilySerializer(family).data, status=status.HTTP_200_OK)


class MyFamilyView(APIView):
    """
    GET /api/v1/family/
    Get the current user's family with all members.
    Returns 404 if the user is not in any family.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FamilySerializer})
    def get(self, request):
        try:
            membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family yet.", "has_family": False},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            **FamilySerializer(membership.family).data,
            "my_role": membership.role,
            "my_nickname": membership.nickname,
            "has_family": True,
        })


class LeaveFamilyView(APIView):
    """
    POST /api/v1/family/leave/
    Leave the current family.
    Admin can only leave if they are the last member (or transfer is handled).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        family = membership.family
        remaining = family.memberships.exclude(user=request.user)

        if membership.role == "admin" and remaining.exists():
            # Transfer admin to the oldest remaining member
            new_admin = remaining.order_by("joined_at").first()
            new_admin.role = "admin"
            new_admin.save(update_fields=["role"])

        membership.delete()

        # If no members left, delete the family
        if not remaining.exists():
            family.delete()

        return Response({"message": "You have left the family."})


class RemoveMemberView(APIView):
    """
    POST /api/v1/family/remove/<member_id>/
    Admin-only: remove a member from the family.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, member_id):
        try:
            my_membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if my_membership.role != "admin":
            return Response(
                {"error": "Only the family admin can remove members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            target = FamilyMembership.objects.get(
                family=my_membership.family,
                user_id=member_id,
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "Member not found in your family."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target.user == request.user:
            return Response(
                {"error": "You cannot remove yourself. Use the leave endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target.delete()
        return Response({"message": "Member removed from family."})


class FamilyNotifyMemberView(APIView):
    """
    POST /api/v1/family/members/<member_id>/notify/
    Sends an in-app notification so the member knows someone wants to reach them (call/alerts).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, member_id):
        try:
            my_membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target = FamilyMembership.objects.select_related("user").get(
                family=my_membership.family,
                user_id=member_id,
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "Member not found in your family."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target.user_id == request.user.id:
            return Response(
                {"error": "You cannot notify yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from community.models import CommunityNotification

        name = request.user.get_full_name() or request.user.email
        CommunityNotification.objects.create(
            user=target.user,
            notification_type="general",
            title="Family is trying to reach you",
            message=f"{name} wants to connect with you from DilCare.",
        )
        return Response({"message": "Notification sent."})


class RegenerateInviteCodeView(APIView):
    """
    POST /api/v1/family/regenerate-code/
    Admin-only: regenerate the family invite code.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role != "admin":
            return Response(
                {"error": "Only the family admin can regenerate the invite code."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_code = membership.family.regenerate_invite_code()
        return Response({
            "invite_code": new_code,
            "message": "Invite code regenerated. Share the new code with family.",
        })


class FamilyMemberHealthView(APIView):
    """
    GET /api/v1/family/members/<member_id>/health/
    View any family member's health summary.
    Both users must be in the same family.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FamilyMemberHealthSummarySerializer})
    def get(self, request, member_id):
        # Verify requester is in a family
        try:
            my_membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify target member is in the same family
        try:
            target_membership = FamilyMembership.objects.select_related("user").get(
                family=my_membership.family,
                user_id=member_id,
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "This person is not in your family."},
                status=status.HTTP_404_NOT_FOUND,
            )

        member = target_membership.user
        health = _get_member_health_data(member)

        data = {
            "member_id": member.id,
            "member_name": member.get_full_name() or member.email,
            "nickname": target_membership.nickname,
            **health,
        }

        return Response(data)


class FamilyPlanView(APIView):
    """
    GET /api/v1/family/plan/
    Returns all available plans with pricing info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "INR",
                "max_members": 4,
                "features": [
                    "Up to 4 family members",
                    "Health tracking for all",
                    "Medicine reminders",
                    "Family health dashboard",
                ],
            },
            {
                "id": "plus",
                "name": "Plus",
                "price": 99,
                "currency": "INR",
                "period": "month",
                "max_members": 6,
                "features": [
                    "Up to 6 family members",
                    "Everything in Free",
                    "Priority AI health assistant",
                    "Advanced health analytics",
                ],
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 199,
                "currency": "INR",
                "period": "month",
                "max_members": 10,
                "features": [
                    "Up to 10 family members",
                    "Everything in Plus",
                    "Doctor consultation credits",
                    "Family health reports",
                    "Priority support",
                ],
            },
        ]

        # Include current plan if user has a family
        current_plan = None
        try:
            membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
            current_plan = membership.family.plan
        except FamilyMembership.DoesNotExist:
            pass

        return Response({
            "plans": plans,
            "current_plan": current_plan,
        })


class UpgradePlanView(APIView):
    """
    POST /api/v1/family/upgrade/
    Admin-only: upgrade the family plan.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            membership = FamilyMembership.objects.select_related("family").get(
                user=request.user
            )
        except FamilyMembership.DoesNotExist:
            return Response(
                {"error": "You are not part of any family."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role != "admin":
            return Response(
                {"error": "Only the family admin can upgrade the plan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpgradePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_plan = serializer.validated_data["plan"]
        family = membership.family

        if new_plan == family.plan:
            return Response(
                {"error": f"You are already on the {new_plan} plan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        family.plan = new_plan
        family.save()  # auto-syncs max_members

        return Response({
            "message": f"Plan upgraded to {new_plan.title()}.",
            "family": FamilySerializer(family).data,
        })
