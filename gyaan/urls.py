"""
Gyaan — URL configuration.
"""
from django.urls import path
from .views import (
    TipListView,
    TipDetailView,
    ToggleFavoriteView,
    MarkCompleteView,
    TipStatsView,
)

urlpatterns = [
    path("tips/", TipListView.as_view(), name="gyaan-tips-list"),
    path("tips/<uuid:pk>/", TipDetailView.as_view(), name="gyaan-tip-detail"),
    path("tips/<uuid:pk>/favorite/", ToggleFavoriteView.as_view(), name="gyaan-tip-favorite"),
    path("tips/<uuid:pk>/complete/", MarkCompleteView.as_view(), name="gyaan-tip-complete"),
    path("stats/", TipStatsView.as_view(), name="gyaan-stats"),
]
