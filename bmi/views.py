"""
BMI — API views for BMI tracking.
"""
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from core.mixins import OwnerQuerySetMixin
from core.permissions import IsOwner
from .models import BMIRecord
from .serializers import BMIRecordSerializer, CreateBMIRecordSerializer


class BMIRecordListCreateView(OwnerQuerySetMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/bmi/        — list all BMI records for the authenticated user (newest first)
    POST /api/v1/bmi/        — create a new BMI record (bmi & category auto-computed)
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateBMIRecordSerializer
        return BMIRecordSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(responses={200: BMIRecordSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=CreateBMIRecordSerializer, responses={201: BMIRecordSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BMIRecordDetailView(OwnerQuerySetMixin, generics.RetrieveDestroyAPIView):
    """
    GET    /api/v1/bmi/{id}/  — retrieve single BMI record
    DELETE /api/v1/bmi/{id}/  — soft-delete a BMI record
    """
    serializer_class = BMIRecordSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    @extend_schema(responses={200: BMIRecordSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(responses={204: None})
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class BMIStatsView(APIView):
    """
    GET /api/v1/bmi/stats/  — latest BMI, average BMI, total records, trend
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        records = BMIRecord.objects.filter(user=request.user).order_by("-date", "-created_at")
        if not records.exists():
            return Response({
                "latest_bmi": None,
                "latest_category": None,
                "average_bmi": None,
                "total_records": 0,
                "trend": None,
            })

        latest = records.first()
        avg_bmi = round(sum(r.bmi for r in records) / records.count(), 1)

        # Trend: compare latest vs previous
        trend = None
        if records.count() >= 2:
            second = records[1]
            diff = latest.bmi - second.bmi
            if diff > 0.1:
                trend = "up"
            elif diff < -0.1:
                trend = "down"
            else:
                trend = "stable"

        return Response({
            "latest_bmi": latest.bmi,
            "latest_category": latest.category,
            "average_bmi": avg_bmi,
            "total_records": records.count(),
            "trend": trend,
        })

