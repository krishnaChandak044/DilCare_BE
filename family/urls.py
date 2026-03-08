"""
Family — URL routes for family linking endpoints.
"""
from django.urls import path

from .views import (
    LinkedParentsListView,
    LinkParentView,
    UnlinkParentView,
    ParentHealthView,
    MyLinkCodeView,
)

app_name = "family"

urlpatterns = [
    # Parents linked to current user (child)
    path("parents/", LinkedParentsListView.as_view(), name="linked-parents"),
    
    # Link to a parent via code
    path("link/", LinkParentView.as_view(), name="link-parent"),
    
    # Unlink from a parent
    path("unlink/<uuid:parent_id>/", UnlinkParentView.as_view(), name="unlink-parent"),
    
    # Get parent's health summary
    path("parents/<uuid:parent_id>/health/", ParentHealthView.as_view(), name="parent-health"),
    
    # Current user's link code (for sharing)
    path("my-code/", MyLinkCodeView.as_view(), name="my-link-code"),
]
