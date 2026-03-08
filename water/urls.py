"""
Water — URL routing for water tracking endpoints.
"""
from django.urls import path
from . import views

app_name = "water"

urlpatterns = [
    # Today's water data
    path("today/", views.TodayWaterView.as_view(), name="today-water"),
    
    # Add/Remove glasses
    path("add/", views.AddGlassView.as_view(), name="add-glass"),
    path("remove/", views.RemoveGlassView.as_view(), name="remove-glass"),
    
    # History and stats
    path("history/", views.WaterHistoryView.as_view(), name="water-history"),
    path("stats/", views.WaterStatsView.as_view(), name="water-stats"),
    
    # Goal management
    path("goal/", views.WaterGoalView.as_view(), name="water-goal"),
    
    # Daily logs (detailed)
    path("logs/", views.DailyWaterLogListView.as_view(), name="water-logs"),
    path("logs/<str:date>/", views.DailyWaterLogDetailView.as_view(), name="water-log-detail"),
]
