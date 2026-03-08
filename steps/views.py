"""
Steps — API views for step tracking, goals, stats, and history.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import StepGoal, DailyStepLog, StepEntry
from .serializers import (
    StepGoalSerializer,
    DailyStepLogSerializer,
    StepEntrySerializer,
    AddManualStepsSerializer,
    StepStatsSerializer,
    WeeklyChartSerializer,
)


def _get_or_create_today_log(user):
    """Get or create today's step log for user."""
    today = timezone.localdate()
    step_goal = StepGoal.objects.filter(user=user).first()
    goal_val = step_goal.daily_goal if step_goal else 10000

    log, created = DailyStepLog.objects.get_or_create(
        user=user,
        date=today,
        defaults={'goal_steps': goal_val}
    )
    
    if not created and log.goal_steps != goal_val:
        log.goal_steps = goal_val
        log.recalculate(step_goal)
        log.save()
    
    return log, step_goal


class TodayStepsView(APIView):
    """
    GET: Get today's step data with computed stats.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: DailyStepLogSerializer})
    def get(self, request):
        log, _ = _get_or_create_today_log(request.user)
        return Response(DailyStepLogSerializer(log).data)


class AddManualStepsView(APIView):
    """
    POST: Add manual steps for today.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AddManualStepsSerializer, responses={200: DailyStepLogSerializer})
    def post(self, request):
        serializer = AddManualStepsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        steps = serializer.validated_data['steps']
        notes = serializer.validated_data.get('notes', '')
        
        log, step_goal = _get_or_create_today_log(request.user)
        
        # Create a step entry record
        StepEntry.objects.create(
            user=request.user,
            steps=steps,
            source='manual',
            notes=notes,
        )
        
        # Update the daily log
        log.manual_steps += steps
        log.recalculate(step_goal)
        log.save()
        
        return Response(DailyStepLogSerializer(log).data)


class RemoveStepsView(APIView):
    """
    POST: Remove steps from today's count (correct mistakes).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        steps = request.data.get('steps', 0)
        try:
            steps = int(steps)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid step count."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if steps <= 0:
            return Response(
                {"error": "Steps must be positive."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        log, step_goal = _get_or_create_today_log(request.user)
        
        log.manual_steps = max(0, log.manual_steps - steps)
        log.recalculate(step_goal)
        log.save()
        
        return Response(DailyStepLogSerializer(log).data)


class StepGoalView(APIView):
    """
    GET: Get current step goal.
    PUT: Update step goal.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: StepGoalSerializer})
    def get(self, request):
        goal, created = StepGoal.objects.get_or_create(
            user=request.user,
            defaults={'daily_goal': 10000}
        )
        return Response(StepGoalSerializer(goal).data)

    @extend_schema(request=StepGoalSerializer, responses={200: StepGoalSerializer})
    def put(self, request):
        goal, created = StepGoal.objects.get_or_create(
            user=request.user,
            defaults={'daily_goal': 10000}
        )
        serializer = StepGoalSerializer(goal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Update today's log to reflect new goal
        today = timezone.localdate()
        today_log = DailyStepLog.objects.filter(user=request.user, date=today).first()
        if today_log:
            today_log.recalculate(goal)
            today_log.save()
        
        return Response(serializer.data)


class StepHistoryView(APIView):
    """
    GET: Get step history for a given number of days.
    Query params: ?days=7 (default: 7)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        days = min(days, 90)  # cap at 90 days

        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)

        logs = DailyStepLog.objects.filter(
            user=request.user,
            date__range=[start_date, today]
        ).order_by('date')

        # Create a complete date range (fill missing days with zeros)
        logs_dict = {log.date: log for log in logs}
        result = []
        step_goal = StepGoal.objects.filter(user=request.user).first()
        goal_val = step_goal.daily_goal if step_goal else 10000

        for i in range(days):
            d = start_date + timedelta(days=i)
            if d in logs_dict:
                result.append(DailyStepLogSerializer(logs_dict[d]).data)
            else:
                result.append({
                    'id': None,
                    'date': d.isoformat(),
                    'total_steps': 0,
                    'manual_steps': 0,
                    'synced_steps': 0,
                    'goal_steps': goal_val,
                    'goal_met': False,
                    'calories_burned': 0,
                    'distance_km': 0,
                    'active_minutes': 0,
                    'source': 'manual',
                    'progress_percent': 0,
                })

        return Response(result)


class StepStatsView(APIView):
    """
    GET: Get comprehensive step statistics.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: StepStatsSerializer})
    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Today
        today_log, _ = _get_or_create_today_log(user)

        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        logs = DailyStepLog.objects.filter(
            user=user,
            date__lte=today
        ).order_by('-date')[:90]

        for i, log in enumerate(logs):
            expected_date = today - timedelta(days=i)
            if log.date == expected_date and log.goal_met:
                current_streak += 1
            else:
                break

        # Calculate longest streak from all logs
        all_met_dates = set(
            DailyStepLog.objects.filter(
                user=user, goal_met=True
            ).values_list('date', flat=True)
        )
        
        if all_met_dates:
            sorted_dates = sorted(all_met_dates)
            temp_streak = 1
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)

        # Week stats (last 7 days)
        week_start = today - timedelta(days=6)
        week_logs = DailyStepLog.objects.filter(
            user=user,
            date__range=[week_start, today]
        )
        week_agg = week_logs.aggregate(
            total=Sum('total_steps'),
            avg=Avg('total_steps'),
            goal_met_count=Count('id', filter=Q(goal_met=True)),
        )

        # Month stats (last 30 days)
        month_start = today - timedelta(days=29)
        month_logs = DailyStepLog.objects.filter(
            user=user,
            date__range=[month_start, today]
        )
        month_agg = month_logs.aggregate(
            total=Sum('total_steps'),
            avg=Avg('total_steps'),
            goal_met_count=Count('id', filter=Q(goal_met=True)),
        )

        progress = 0.0
        if today_log.goal_steps > 0:
            progress = round(min((today_log.total_steps / today_log.goal_steps) * 100, 100), 1)

        data = {
            'today_steps': today_log.total_steps,
            'today_goal': today_log.goal_steps,
            'today_progress': progress,
            'today_calories': today_log.calories_burned,
            'today_distance_km': today_log.distance_km,
            'today_active_minutes': today_log.active_minutes,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'week_total_steps': week_agg['total'] or 0,
            'week_avg_steps': int(week_agg['avg'] or 0),
            'week_days_goal_met': week_agg['goal_met_count'] or 0,
            'month_total_steps': month_agg['total'] or 0,
            'month_avg_steps': int(month_agg['avg'] or 0),
            'month_days_goal_met': month_agg['goal_met_count'] or 0,
        }

        return Response(data)


class WeeklyChartView(APIView):
    """
    GET: Get weekly chart data for the bar chart.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: WeeklyChartSerializer})
    def get(self, request):
        today = timezone.localdate()
        
        # Get Monday of current week
        weekday = today.weekday()  # 0=Monday
        monday = today - timedelta(days=weekday)
        
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        data = [0] * 7
        goals = [10000] * 7
        
        step_goal = StepGoal.objects.filter(user=request.user).first()
        goal_val = step_goal.daily_goal if step_goal else 10000
        goals = [goal_val] * 7
        
        logs = DailyStepLog.objects.filter(
            user=request.user,
            date__range=[monday, monday + timedelta(days=6)]
        )
        
        for log in logs:
            day_index = (log.date - monday).days
            if 0 <= day_index < 7:
                data[day_index] = log.total_steps
        
        return Response({
            'labels': labels,
            'data': data,
            'goals': goals,
        })


class StepEntriesView(APIView):
    """
    GET: Get individual step entries for today.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        entries = StepEntry.objects.filter(
            user=request.user,
            date=today,
            is_deleted=False
        ).order_by('-recorded_at')
        
        return Response(StepEntrySerializer(entries, many=True).data)
