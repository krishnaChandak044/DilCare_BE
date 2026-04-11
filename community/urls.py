"""
Community — URL routes for community endpoints.
"""
from django.urls import path
from .views import (
    LeaderboardView,
    GroupListCreateView, GroupDetailView,
    GroupMembersView, JoinGroupView, LeaveGroupView,
    GroupRoleUpdateView, GroupMemberRemoveView,
    GroupChatView, GroupChatUnreadView,
    ChallengeListCreateView, ChallengeDetailView,
    JoinChallengeView, LeaveChallengeView,
    ChallengeParticipantsView, RefreshChallengeProgressView,
    NotificationListView, MarkNotificationReadView,
    MarkAllNotificationsReadView, UnreadNotificationCountView,
    UserCommunityPreferenceView, GroupNotificationPreferenceView,
    UserBadgeListView, MilestoneSyncView,
    ModerationReportListCreateView,
    FeedListCreateView, FeedLikeToggleView, FeedCommentListCreateView,
)

app_name = "community"

urlpatterns = [
    # ── Leaderboard (Steps Integration) ─────────────────────
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),

    # ── Groups ──────────────────────────────────────────────
    path("groups/", GroupListCreateView.as_view(), name="group-list-create"),
    path("groups/<uuid:pk>/", GroupDetailView.as_view(), name="group-detail"),
    path("groups/<uuid:pk>/members/", GroupMembersView.as_view(), name="group-members"),
    path("groups/<uuid:pk>/roles/", GroupRoleUpdateView.as_view(), name="group-roles-update"),
    path("groups/<uuid:pk>/members/<uuid:member_id>/remove/", GroupMemberRemoveView.as_view(), name="group-member-remove"),
    path("groups/<uuid:pk>/leave/", LeaveGroupView.as_view(), name="group-leave"),
    path("groups/<uuid:pk>/chat/", GroupChatView.as_view(), name="group-chat"),
    path("groups/chat/unread/", GroupChatUnreadView.as_view(), name="group-chat-unread"),
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
    path("notifications/preferences/", UserCommunityPreferenceView.as_view(), name="notification-preferences"),
    path("notifications/group-preferences/", GroupNotificationPreferenceView.as_view(), name="notification-group-preferences"),

    # ── Achievements / Moderation / Milestones ───────────
    path("badges/me/", UserBadgeListView.as_view(), name="user-badges"),
    path("feed/milestones/sync/", MilestoneSyncView.as_view(), name="feed-milestones-sync"),
    path("moderation/reports/", ModerationReportListCreateView.as_view(), name="moderation-reports"),

    # ── Feed ───────────────────────────────────────────────
    path("feed/", FeedListCreateView.as_view(), name="feed-list-create"),
    path("feed/<uuid:pk>/like/", FeedLikeToggleView.as_view(), name="feed-like-toggle"),
    path("feed/<uuid:pk>/comments/", FeedCommentListCreateView.as_view(), name="feed-comments"),
]
