"""
Community — URL routes for community endpoints.
"""
from django.urls import path
from .views import (
    LeaderboardView,
    GroupListCreateView, GroupDetailView,
    GroupMembersView, JoinGroupView, LeaveGroupView,
    ChallengeListCreateView, ChallengeDetailView,
    JoinChallengeView, LeaveChallengeView,
    ChallengeParticipantsView, RefreshChallengeProgressView,
    NotificationListView, MarkNotificationReadView,
    MarkAllNotificationsReadView, UnreadNotificationCountView,
)

app_name = "community"

urlpatterns = [
    # ── Leaderboard (Steps Integration) ─────────────────────
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),

    # ── Groups ──────────────────────────────────────────────
    path("groups/", GroupListCreateView.as_view(), name="group-list-create"),
    path("groups/<uuid:pk>/", GroupDetailView.as_view(), name="group-detail"),
    path("groups/<uuid:pk>/members/", GroupMembersView.as_view(), name="group-members"),
    path("groups/<uuid:pk>/leave/", LeaveGroupView.as_view(), name="group-leave"),
    path("groups/join/", JoinGroupView.as_view(), name="group-join"),

    # ── Challenges ──────────────────────────────────────────
    path("challenges/", ChallengeListCreateView.as_view(), name="challenge-list-create"),
    path("challenges/<uuid:pk>/", ChallengeDetailView.as_view(), name="challenge-detail"),
    path("challenges/<uuid:pk>/join/", JoinChallengeView.as_view(), name="challenge-join"),
    path("challenges/<uuid:pk>/leave/", LeaveChallengeView.as_view(), name="challenge-leave"),
    path("challenges/<uuid:pk>/participants/", ChallengeParticipantsView.as_view(), name="challenge-participants"),
    path("challenges/<uuid:pk>/refresh/", RefreshChallengeProgressView.as_view(), name="challenge-refresh"),

    # ── Notifications ───────────────────────────────────────
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<uuid:pk>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
    path("notifications/read-all/", MarkAllNotificationsReadView.as_view(), name="notifications-read-all"),
    path("notifications/unread-count/", UnreadNotificationCountView.as_view(), name="notifications-unread-count"),
]
