"""
Health — API Views for health readings.
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from collections import defaultdict

from core.mixins import OwnerQuerySetMixin
from .models import HealthReading, HealthGoal
from .serializers import (
    HealthReadingSerializer,
    HealthReadingCreateSerializer,
    HealthSummarySerializer,
    HealthGoalSerializer,
    HealthTrendSerializer,
)


class HealthReadingListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/health/readings/  → List user's health readings
    POST /api/v1/health/readings/  → Add a new reading
    
    Query params:
    - type: Filter by reading type (bp, sugar, weight, heartRate)
    - start_date: Filter readings from this date (YYYY-MM-DD)
    - end_date: Filter readings until this date (YYYY-MM-DD)
    - limit: Limit number of results
    """
    permission_classes = [IsAuthenticated]
    queryset = HealthReading.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HealthReadingCreateSerializer
        return HealthReadingSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by type
        reading_type = self.request.query_params.get('type')
        if reading_type:
            qs = qs.filter(reading_type=reading_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            qs = qs.filter(recorded_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(recorded_at__date__lte=end_date)
        
        # Limit results
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                qs = qs[:int(limit)]
            except ValueError:
                pass
        
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reading = serializer.save()
        
        # Return the full reading data
        output_serializer = HealthReadingSerializer(reading)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class HealthReadingDetailView(OwnerQuerySetMixin, generics.RetrieveDestroyAPIView):
    """
    GET    /api/v1/health/readings/{id}/  → Get a specific reading
    DELETE /api/v1/health/readings/{id}/  → Soft delete a reading
    """
    permission_classes = [IsAuthenticated]
    queryset = HealthReading.objects.all()
    serializer_class = HealthReadingSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HealthSummaryView(APIView):
    """
    GET /api/v1/health/summary/  → Get latest reading of each type
    
    Returns the most recent reading for each health type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        summary = []
        
        for reading_type, label in HealthReading.READING_TYPES:
            latest = HealthReading.objects.filter(
                user=user,
                reading_type=reading_type
            ).order_by('-recorded_at').first()
            
            if latest:
                summary.append({
                    'type': latest.reading_type,
                    'value': latest.value,
                    'unit': latest.unit,
                    'status': latest.status,
                    'recorded_at': latest.recorded_at,
                    'date': latest.recorded_at.strftime('%d %b %Y'),
                    'time': latest.recorded_at.strftime('%I:%M %p'),
                })
            else:
                # Return empty placeholder for types with no readings
                summary.append({
                    'type': reading_type,
                    'value': '--',
                    'unit': HealthReading.UNITS.get(reading_type, ''),
                    'status': 'normal',
                    'recorded_at': None,
                    'date': None,
                    'time': None,
                })
        
        serializer = HealthSummarySerializer(summary, many=True)
        return Response(serializer.data)


class HealthTrendsView(APIView):
    """
    GET /api/v1/health/trends/  → Get weekly trends for chart
    
    Query params:
    - type: Reading type (default: bp)
    - period: 'week' or 'month' (default: week)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        reading_type = request.query_params.get('type', 'bp')
        period = request.query_params.get('period', 'week')
        
        # Determine date range
        end_date = timezone.now()
        if period == 'month':
            start_date = end_date - timedelta(days=30)
            num_points = 30
        else:
            start_date = end_date - timedelta(days=7)
            num_points = 7
        
        # Get readings in range
        readings = HealthReading.objects.filter(
            user=user,
            reading_type=reading_type,
            recorded_at__gte=start_date,
            recorded_at__lte=end_date
        ).order_by('recorded_at')
        
        # Group by date
        data_by_date = defaultdict(list)
        for reading in readings:
            date_key = reading.recorded_at.strftime('%Y-%m-%d')
            data_by_date[date_key].append(reading.value_primary)
        
        # Build labels and data arrays
        labels = []
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            if period == 'month':
                labels.append(current_date.strftime('%d'))
            else:
                labels.append(current_date.strftime('%a'))
            
            if date_key in data_by_date:
                # Average if multiple readings on same day
                avg_val = sum(data_by_date[date_key]) / len(data_by_date[date_key])
                data.append(round(avg_val, 1))
            else:
                data.append(None)
            
            current_date += timedelta(days=1)
        
        response_data = {
            'labels': labels,
            'data': data,
            'reading_type': reading_type,
        }
        
        serializer = HealthTrendSerializer(response_data)
        return Response(serializer.data)


class HealthGoalListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/health/goals/  → Get health goals
    POST /api/v1/health/goals/  → Create/update health goal
    """
    permission_classes = [IsAuthenticated]
    queryset = HealthGoal.objects.all()
    serializer_class = HealthGoalSerializer

    def create(self, request, *args, **kwargs):
        reading_type = request.data.get('type') or request.data.get('reading_type')
        
        # Update or create
        goal, created = HealthGoal.objects.update_or_create(
            user=request.user,
            reading_type=reading_type,
            defaults={
                'min_value': request.data.get('min_value'),
                'max_value': request.data.get('max_value'),
                'target_value': request.data.get('target_value'),
            }
        )
        
        serializer = self.get_serializer(goal)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)
