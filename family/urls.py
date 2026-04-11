"""
Family — URL routes for family group endpoints.
"""
from django.urls import path

from .views import (
    CreateFamilyView,
    JoinFamilyView,
    MyFamilyView,
    LeaveFamilyView,
    RemoveMemberView,
    FamilyNotifyMemberView,
    RegenerateInviteCodeView,
    FamilyMemberHealthView,
    FamilyPlanView,
    UpgradePlanView,
)

app_name = "family"

urlpatterns = [
    # Family CRUD
    path("", MyFamilyView.as_view(), name="my-family"),
    path("create/", CreateFamilyView.as_view(), name="create-family"),
    path("join/", JoinFamilyView.as_view(), name="join-family"),
    path("leave/", LeaveFamilyView.as_view(), name="leave-family"),

    # Plan management
    path("plan/", FamilyPlanView.as_view(), name="family-plan"),
    path("upgrade/", UpgradePlanView.as_view(), name="upgrade-plan"),

    # Admin actions
    path("remove/<int:member_id>/", RemoveMemberView.as_view(), name="remove-member"),
    path("regenerate-code/", RegenerateInviteCodeView.as_view(), name="regenerate-code"),

    # View any family member's health
    path("members/<int:member_id>/health/", FamilyMemberHealthView.as_view(), name="member-health"),
    path("members/<int:member_id>/notify/", FamilyNotifyMemberView.as_view(), name="member-notify"),
]
