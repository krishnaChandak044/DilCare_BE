"""
Steps — URL routes for step tracking endpoints.
"""
from django.urls import path
from .views import (
    TodayStepsView,
    AddManualStepsView,
    RemoveStepsView,
    StepGoalView,
    StepHistoryView,
    StepStatsView,
    WeeklyChartView,
    StepEntriesView,
)

app_name = "steps"

urlpatterns = [
    # Today's steps
    path("today/", TodayStepsView.as_view(), name="today"),
    
    # Add/Remove steps
    path("add/", AddManualStepsView.as_view(), name="add-steps"),
    path("remove/", RemoveStepsView.as_view(), name="remove-steps"),
    
    # Goal management
    path("goal/", StepGoalView.as_view(), name="goal"),
    
    # History and stats
    path("history/", StepHistoryView.as_view(), name="history"),
    path("stats/", StepStatsView.as_view(), name="stats"),
    path("weekly-chart/", WeeklyChartView.as_view(), name="weekly-chart"),
    
    # Entries
    path("entries/", StepEntriesView.as_view(), name="entries"),
]
