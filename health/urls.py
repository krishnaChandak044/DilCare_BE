"""
Health — URL routes for /api/v1/health/
"""
from django.urls import path
from .views import (
    HealthReadingListCreateView,
    HealthReadingDetailView,
    HealthSummaryView,
    HealthTrendsView,
    HealthGoalListCreateView,
)

urlpatterns = [
    path('readings/', HealthReadingListCreateView.as_view(), name='health-readings'),
    path('readings/<uuid:pk>/', HealthReadingDetailView.as_view(), name='health-reading-detail'),
    path('summary/', HealthSummaryView.as_view(), name='health-summary'),
    path('trends/', HealthTrendsView.as_view(), name='health-trends'),
    path('goals/', HealthGoalListCreateView.as_view(), name='health-goals'),
]
