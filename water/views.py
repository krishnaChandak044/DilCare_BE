"""
Water — API views for water intake tracking.
"""
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.mixins import OwnerQuerySetMixin
from core.permissions import IsOwner
from .models import WaterGoal, DailyWaterLog, WaterIntakeEntry
from .serializers import (
    WaterGoalSerializer,
    DailyWaterLogSerializer,
    TodayWaterSerializer,
    AddGlassSerializer,
    WaterHistorySerializer,
    WaterStatsSerializer,
)


def get_or_create_today_log(user):
    """Get or create today's water log for a user."""
    today = timezone.localdate()
    
    # Get user's active goal
    goal = WaterGoal.objects.filter(user=user, is_active=True).first()
    goal_glasses = goal.daily_glasses if goal else 8
    glass_size_ml = goal.glass_size_ml if goal else 250
    
    log, created = DailyWaterLog.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            "goal_glasses": goal_glasses,
            "glass_size_ml": glass_size_ml,
        }
    )
    return log


def calculate_streak(user):
    """Calculate current streak of days meeting water goal."""
    today = timezone.localdate()
    streak = 0
    current_date = today - timedelta(days=1)  # Start from yesterday
    
    # Check if today's goal is met
    today_log = DailyWaterLog.objects.filter(user=user, date=today, goal_reached=True).first()
    if today_log:
        streak = 1
        current_date = today - timedelta(days=1)
    
    # Count consecutive days before today
    while True:
        log = DailyWaterLog.objects.filter(user=user, date=current_date, goal_reached=True).first()
        if log:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak


# ============ Today's Water Data ============

class TodayWaterView(APIView):
    """
    GET: Get today's water intake data with goal and streak.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: TodayWaterSerializer})
    def get(self, request):
        log = get_or_create_today_log(request.user)
        goal = WaterGoal.objects.filter(user=request.user, is_active=True).first()
        streak = calculate_streak(request.user)

        data = {
            "date": log.date,
            "glasses": log.glasses,
            "goal_glasses": log.goal_glasses,
            "glass_size_ml": log.glass_size_ml,
            "total_ml": log.total_ml,
            "progress_percent": log.progress_percent,
            "goal_reached": log.goal_reached,
            "streak": streak,
            "reminder_enabled": goal.reminder_enabled if goal else False,
        }

        return Response(data)


class AddGlassView(APIView):
    """
    POST: Add one or more glasses of water to today's intake.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddGlassSerializer,
        responses={200: TodayWaterSerializer}
    )
    def post(self, request):
        serializer = AddGlassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = serializer.validated_data.get("count", 1)
        notes = serializer.validated_data.get("notes", "")

        log = get_or_create_today_log(request.user)
        log.add_glass(count)

        # Create entry for detailed tracking
        WaterIntakeEntry.objects.create(
            daily_log=log,
            glasses=count,
            notes=notes,
        )

        goal = WaterGoal.objects.filter(user=request.user, is_active=True).first()
        streak = calculate_streak(request.user)

        data = {
            "date": log.date,
            "glasses": log.glasses,
            "goal_glasses": log.goal_glasses,
            "glass_size_ml": log.glass_size_ml,
            "total_ml": log.total_ml,
            "progress_percent": log.progress_percent,
            "goal_reached": log.goal_reached,
            "streak": streak,
            "reminder_enabled": goal.reminder_enabled if goal else False,
        }

        return Response(data)


class RemoveGlassView(APIView):
    """
    POST: Remove one or more glasses from today's intake.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddGlassSerializer,
        responses={200: TodayWaterSerializer}
    )
    def post(self, request):
        serializer = AddGlassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = serializer.validated_data.get("count", 1)

        log = get_or_create_today_log(request.user)
        log.remove_glass(count)

        goal = WaterGoal.objects.filter(user=request.user, is_active=True).first()
        streak = calculate_streak(request.user)

        data = {
            "date": log.date,
            "glasses": log.glasses,
            "goal_glasses": log.goal_glasses,
            "glass_size_ml": log.glass_size_ml,
            "total_ml": log.total_ml,
            "progress_percent": log.progress_percent,
            "goal_reached": log.goal_reached,
            "streak": streak,
            "reminder_enabled": goal.reminder_enabled if goal else False,
        }

        return Response(data)


# ============ History & Stats ============

class WaterHistoryView(APIView):
    """
    GET: Get water intake history.
    Query params: days (default: 7)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="days", type=int, description="Number of days to retrieve (default: 7)")
        ],
        responses={200: WaterHistorySerializer(many=True)}
    )
    def get(self, request):
        days = int(request.query_params.get("days", 7))
        days = min(days, 90)  # Max 90 days

        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)

        logs = DailyWaterLog.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=today
        ).order_by("date")

        # Fill in missing days with zero values
        result = []
        current_date = start_date
        logs_dict = {log.date: log for log in logs}
        
        goal = WaterGoal.objects.filter(user=request.user, is_active=True).first()
        default_goal = goal.daily_glasses if goal else 8
        default_glass_ml = goal.glass_size_ml if goal else 250

        while current_date <= today:
            if current_date in logs_dict:
                log = logs_dict[current_date]
                result.append({
                    "date": log.date,
                    "glasses": log.glasses,
                    "goal_glasses": log.goal_glasses,
                    "total_ml": log.total_ml,
                    "progress_percent": log.progress_percent,
                    "goal_reached": log.goal_reached,
                })
            else:
                result.append({
                    "date": current_date,
                    "glasses": 0,
                    "goal_glasses": default_goal,
                    "total_ml": 0,
                    "progress_percent": 0,
                    "goal_reached": False,
                })
            current_date += timedelta(days=1)

        return Response(result)


class WaterStatsView(APIView):
    """
    GET: Get water intake statistics.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: WaterStatsSerializer})
    def get(self, request):
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Calculate streaks
        current_streak = calculate_streak(request.user)
        
        # Calculate longest streak (simplified - scan last 90 days)
        longest_streak = 0
        temp_streak = 0
        for i in range(90, -1, -1):
            date = today - timedelta(days=i)
            log = DailyWaterLog.objects.filter(user=request.user, date=date, goal_reached=True).first()
            if log:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        # 7-day stats
        week_logs = DailyWaterLog.objects.filter(
            user=request.user,
            date__gte=week_ago,
            date__lte=today
        )
        week_agg = week_logs.aggregate(
            total=Sum("glasses"),
            avg=Avg("glasses"),
            goals_met=Count("id", filter=Q(goal_reached=True))
        )

        # 30-day stats
        month_logs = DailyWaterLog.objects.filter(
            user=request.user,
            date__gte=month_ago,
            date__lte=today
        )
        month_agg = month_logs.aggregate(
            total=Sum("glasses"),
            avg=Avg("glasses"),
            goals_met=Count("id", filter=Q(goal_reached=True))
        )

        data = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_glasses_7d": week_agg["total"] or 0,
            "total_glasses_30d": month_agg["total"] or 0,
            "avg_glasses_7d": round(week_agg["avg"] or 0, 1),
            "avg_glasses_30d": round(month_agg["avg"] or 0, 1),
            "goals_met_7d": week_agg["goals_met"] or 0,
            "goals_met_30d": month_agg["goals_met"] or 0,
        }

        return Response(data)


# ============ Goal Management ============

class WaterGoalView(APIView):
    """
    GET: Get active water goal.
    PUT: Update or create water goal.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: WaterGoalSerializer})
    def get(self, request):
        goal = WaterGoal.objects.filter(user=request.user, is_active=True).first()
        if not goal:
            # Return default values
            return Response({
                "id": None,
                "daily_glasses": 8,
                "glass_size_ml": 250,
                "daily_target_ml": 2000,
                "reminder_enabled": False,
                "reminder_interval_hours": 2,
                "is_active": True,
            })
        return Response(WaterGoalSerializer(goal).data)

    @extend_schema(request=WaterGoalSerializer, responses={200: WaterGoalSerializer})
    def put(self, request):
        goal = WaterGoal.objects.filter(user=request.user, is_active=True).first()
        
        if goal:
            serializer = WaterGoalSerializer(goal, data=request.data, partial=True)
        else:
            serializer = WaterGoalSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, is_active=True)
        
        return Response(serializer.data)


# ============ Daily Logs CRUD (for admin/detailed view) ============

class DailyWaterLogListView(OwnerQuerySetMixin, generics.ListAPIView):
    """
    GET: List all water logs for the authenticated user.
    """
    queryset = DailyWaterLog.objects.all()
    serializer_class = DailyWaterLogSerializer
    permission_classes = [IsAuthenticated]
    owner_field = "user"

    def get_queryset(self):
        qs = DailyWaterLog.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        
        return qs


class DailyWaterLogDetailView(OwnerQuerySetMixin, generics.RetrieveAPIView):
    """
    GET: Retrieve a specific water log.
    """
    queryset = DailyWaterLog.objects.all()
    serializer_class = DailyWaterLogSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    owner_field = "user"
    lookup_field = "date"

    def get_queryset(self):
        return DailyWaterLog.objects.filter(user=self.request.user)
