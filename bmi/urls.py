"""
BMI — URL configuration.
"""
from django.urls import path
from .views import BMIRecordListCreateView, BMIRecordDetailView, BMIStatsView

urlpatterns = [
    path("", BMIRecordListCreateView.as_view(), name="bmi-list-create"),
    path("stats/", BMIStatsView.as_view(), name="bmi-stats"),
    path("<uuid:pk>/", BMIRecordDetailView.as_view(), name="bmi-detail"),
]
