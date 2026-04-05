"""
Community — API views for leaderboard, groups, challenges & notifications.

Integrates with Steps app for step-based leaderboards and challenge progress.
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    CommunityGroup, GroupMembership,
    Challenge, ChallengeParticipant,
    CommunityNotification,
)
from .serializers import (
    CommunityGroupSerializer, CreateGroupSerializer, JoinGroupSerializer,
    GroupMemberSerializer,
    ChallengeSerializer, CreateChallengeSerializer, ChallengeParticipantSerializer,
    LeaderboardSerializer,
    CommunityNotificationSerializer,
)

User = get_user_model()


def can_view_challenge(user, challenge):
    if challenge.is_public or challenge.created_by_id == user.id:
        return True

    if challenge.group_id:
        return GroupMembership.objects.filter(
            group_id=challenge.group_id,
            user=user,
            is_active=True,
        ).exists()

    return ChallengeParticipant.objects.filter(
        challenge=challenge,
        user=user,
    ).exists()


# LEADERBOARD — Computed from Steps DailyStepLog

class LeaderboardView(APIView):
    """
    GET: Get step-based leaderboard.
    Query params:
      - period: 'today' | 'week' | 'month' | 'all' (default: week)
      - group: UUID of a group to filter by
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='period', type=str, enum=['today', 'week', 'month', 'all']),
            OpenApiParameter(name='group', type=str, required=False),
        ],
        responses={200: LeaderboardSerializer},
    )
    def get(self, request):
        from steps.models import DailyStepLog

        period = request.query_params.get('period', 'week')
        group_id = request.query_params.get('group')
        today = timezone.localdate()

        # Determine date range
        period_config = {
            'today': (today, today, 'Today'),
            'week': (today - timedelta(days=6), today, 'This Week'),
            'month': (today - timedelta(days=29), today, 'This Month'),
            'all': (None, None, 'All Time'),
        }
        start_date, end_date, period_label = period_config.get(
            period, period_config['week']
        )

        # Base queryset
        qs = DailyStepLog.objects.all()
        if start_date:
            qs = qs.filter(date__gte=start_date, date__lte=end_date)

        # Filter by group members if group specified
        if group_id:
            member_ids = GroupMembership.objects.filter(
                group_id=group_id, is_active=True
            ).values_list('user_id', flat=True)
            qs = qs.filter(user_id__in=member_ids)

        # Aggregate per user
        user_stats = (
            qs.values('user')
            .annotate(
                total_steps_sum=Sum('total_steps'),
                avg_steps=Avg('total_steps'),
                days_active=Count('id'),
            )
            .order_by('-total_steps_sum')[:50]
        )

        # Build leaderboard entries with rank
        entries = []
        my_rank = None
        my_steps = 0
        user_ids = [s['user'] for s in user_stats]
        user_map = {
            u.id: u.get_full_name() or u.email
            for u in User.objects.filter(id__in=user_ids)
        }

        for rank, stat in enumerate(user_stats, 1):
            uid = stat['user']
            is_self = uid == request.user.id
            if is_self:
                my_rank = rank
                my_steps = stat['total_steps_sum']

            entries.append({
                'rank': rank,
                'user_id': uid,
                'user_name': user_map.get(uid, 'Unknown'),
                'total_steps': stat['total_steps_sum'],
                'avg_steps': round(stat['avg_steps'] or 0),
                'days_active': stat['days_active'],
                'is_self': is_self,
            })

        # If current user not in top 50, find their rank
        if my_rank is None:
            my_qs = qs.filter(user=request.user)
            my_agg = my_qs.aggregate(total=Sum('total_steps'))
            my_steps = my_agg['total'] or 0

        data = {
            'period': period,
            'period_label': period_label,
            'entries': entries,
            'my_rank': my_rank,
            'my_steps': my_steps,
            'total_participants': len(entries),
        }

        serializer = LeaderboardSerializer(instance=data)
        return Response(serializer.data)


# ═════════════════════════════════════════════════════════════════════
# GROUPS
# ═════════════════════════════════════════════════════════════════════

class GroupListCreateView(APIView):
    """
    GET:  List groups the user is a member of + public discoverable groups.
    POST: Create a new group (creator becomes admin).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CommunityGroupSerializer(many=True)})
    def get(self, request):
        my_group_ids = GroupMembership.objects.filter(
            user=request.user, is_active=True
        ).values_list('group_id', flat=True)

        groups = CommunityGroup.objects.filter(
            Q(id__in=my_group_ids) | Q(is_public=True)
        ).distinct()

        serializer = CommunityGroupSerializer(
            groups, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @extend_schema(request=CreateGroupSerializer, responses={201: CommunityGroupSerializer})
    def post(self, request):
        serializer = CreateGroupSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(
            CommunityGroupSerializer(group, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class GroupDetailView(APIView):
    """
    GET:    Retrieve group details.
    PATCH:  Update group (admin only).
    DELETE: Soft-delete group (admin only).
    """
    permission_classes = [IsAuthenticated]

    def _get_group(self, pk):
        try:
            return CommunityGroup.objects.get(pk=pk, deleted_at__isnull=True)
        except CommunityGroup.DoesNotExist:
            return None

    def _is_admin(self, user, group):
        return GroupMembership.objects.filter(
            user=user, group=group, role='admin', is_active=True
        ).exists()

    def _is_member(self, user, group):
        return GroupMembership.objects.filter(
            user=user, group=group, is_active=True
        ).exists()

    def _can_view_group(self, user, group):
        return group.is_public or self._is_member(user, group)

    @extend_schema(responses={200: CommunityGroupSerializer})
    def get(self, request, pk):
        group = self._get_group(pk)
        if not group:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_view_group(request.user, group):
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            CommunityGroupSerializer(group, context={'request': request}).data
        )

    @extend_schema(request=CreateGroupSerializer, responses={200: CommunityGroupSerializer})
    def patch(self, request, pk):
        group = self._get_group(pk)
        if not group:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_admin(request.user, group):
            return Response({"error": "Only admins can edit the group."}, status=status.HTTP_403_FORBIDDEN)

        for field in ['name', 'description', 'icon', 'color', 'is_public', 'max_members']:
            if field in request.data:
                setattr(group, field, request.data[field])
        group.save()
        return Response(
            CommunityGroupSerializer(group, context={'request': request}).data
        )

    def delete(self, request, pk):
        group = self._get_group(pk)
        if not group:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._is_admin(request.user, group):
            return Response({"error": "Only admins can delete the group."}, status=status.HTTP_403_FORBIDDEN)
        group.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupMembersView(APIView):
    """
    GET: List members of a group.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: GroupMemberSerializer(many=True)})
    def get(self, request, pk):
        try:
            group = CommunityGroup.objects.get(pk=pk, deleted_at__isnull=True)
        except CommunityGroup.DoesNotExist:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        is_member = GroupMembership.objects.filter(
            group=group, user=request.user, is_active=True
        ).exists()
        if not is_member:
            return Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        memberships = GroupMembership.objects.filter(
            group_id=pk, is_active=True
        ).select_related('user')
        serializer = GroupMemberSerializer(memberships, many=True)
        return Response(serializer.data)


class JoinGroupView(APIView):
    """
    POST: Join a group (public groups directly, private via invite code).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=JoinGroupSerializer, responses={200: CommunityGroupSerializer})
    def post(self, request):
        serializer = JoinGroupSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        group = serializer.group

        membership, created = GroupMembership.objects.get_or_create(
            user=request.user, group=group,
            defaults={'role': 'member'}
        )
        if not created and not membership.is_active:
            membership.is_active = True
            membership.save(update_fields=['is_active'])

        # Send notification to group admin
        CommunityNotification.objects.create(
            user=group.created_by,
            notification_type='group_joined',
            title=f'{request.user.get_full_name() or request.user.email} joined {group.name}',
            message=f'A new member has joined your group.',
            related_group=group,
        )

        return Response(
            CommunityGroupSerializer(group, context={'request': request}).data
        )


class LeaveGroupView(APIView):
    """
    POST: Leave a group.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        membership = GroupMembership.objects.filter(
            user=request.user, group_id=pk, is_active=True
        ).first()

        if not membership:
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if membership.role == 'admin':
            # Check if there are other admins
            other_admins = GroupMembership.objects.filter(
                group_id=pk, role='admin', is_active=True
            ).exclude(user=request.user).count()
            if other_admins == 0:
                return Response(
                    {"error": "You are the only admin. Transfer admin role before leaving."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        membership.is_active = False
        membership.save(update_fields=['is_active'])
        return Response({"message": "You have left the group."})


# ═════════════════════════════════════════════════════════════════════
# CHALLENGES
# ═════════════════════════════════════════════════════════════════════

class ChallengeListCreateView(APIView):
    """
    GET:  List available challenges (public + my groups' challenges).
    POST: Create a new challenge.
    Query params:
      - status: 'active' | 'upcoming' | 'completed'
      - type: 'steps' | 'water' | 'medicine' | 'custom'
      - joined: 'true' for only challenges the user has joined
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='status', type=str, required=False),
            OpenApiParameter(name='type', type=str, required=False),
            OpenApiParameter(name='joined', type=str, required=False),
        ],
        responses={200: ChallengeSerializer(many=True)},
    )
    def get(self, request):
        # Auto-update statuses
        today = timezone.localdate()
        Challenge.objects.filter(
            status='upcoming', start_date__lte=today
        ).update(status='active')
        Challenge.objects.filter(
            status='active', end_date__lt=today
        ).update(status='completed')

        # Build queryset
        my_group_ids = GroupMembership.objects.filter(
            user=request.user, is_active=True
        ).values_list('group_id', flat=True)

        qs = Challenge.objects.filter(
            Q(is_public=True) |
            Q(group_id__in=my_group_ids) |
            Q(created_by=request.user)
        ).distinct()

        # Filters
        challenge_status = request.query_params.get('status')
        if challenge_status:
            qs = qs.filter(status=challenge_status)

        challenge_type = request.query_params.get('type')
        if challenge_type:
            qs = qs.filter(challenge_type=challenge_type)

        joined_only = request.query_params.get('joined')
        if joined_only == 'true':
            my_challenge_ids = ChallengeParticipant.objects.filter(
                user=request.user
            ).values_list('challenge_id', flat=True)
            qs = qs.filter(id__in=my_challenge_ids)

        serializer = ChallengeSerializer(
            qs, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @extend_schema(request=CreateChallengeSerializer, responses={201: ChallengeSerializer})
    def post(self, request):
        serializer = CreateChallengeSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        challenge = serializer.save()
        return Response(
            ChallengeSerializer(challenge, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class ChallengeDetailView(APIView):
    """
    GET:    Retrieve challenge details.
    DELETE: Cancel a challenge (creator only).
    """
    permission_classes = [IsAuthenticated]

    def _get_challenge(self, pk):
        try:
            return Challenge.objects.get(pk=pk, deleted_at__isnull=True)
        except Challenge.DoesNotExist:
            return None

    @extend_schema(responses={200: ChallengeSerializer})
    def get(self, request, pk):
        challenge = self._get_challenge(pk)
        if not challenge:
            return Response({"error": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND)
        if not can_view_challenge(request.user, challenge):
            return Response({"error": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND)
        challenge.auto_update_status()
        return Response(
            ChallengeSerializer(challenge, context={'request': request}).data
        )

    def delete(self, request, pk):
        challenge = self._get_challenge(pk)
        if not challenge:
            return Response({"error": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND)
        if challenge.created_by != request.user:
            return Response({"error": "Only the creator can cancel this challenge."}, status=status.HTTP_403_FORBIDDEN)
        challenge.status = 'cancelled'
        challenge.save(update_fields=['status'])
        return Response({"message": "Challenge cancelled."})


class JoinChallengeView(APIView):
    """
    POST: Join a challenge.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk, deleted_at__isnull=True)
        except Challenge.DoesNotExist:
            return Response({"error": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND)

        if not can_view_challenge(request.user, challenge):
            return Response({"error": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND)

        if challenge.status not in ('upcoming', 'active'):
            return Response(
                {"error": "Cannot join a completed or cancelled challenge."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if challenge.participants.count() >= challenge.max_participants:
            return Response(
                {"error": "Challenge is full."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant, created = ChallengeParticipant.objects.get_or_create(
            user=request.user, challenge=challenge,
        )

        if not created:
            return Response(
                {"error": "You have already joined this challenge."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Compute initial progress
        participant.refresh_progress()

        return Response(
            ChallengeSerializer(challenge, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class LeaveChallengeView(APIView):
    """
    POST: Leave a challenge.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        participant = ChallengeParticipant.objects.filter(
            user=request.user, challenge_id=pk
        ).first()

        if not participant:
            return Response(
                {"error": "You haven't joined this challenge."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant.soft_delete()
        return Response({"message": "You have left the challenge."})


class ChallengeParticipantsView(APIView):
    """
    GET: List participants of a challenge with their progress.
    Refreshes step/water progress for all participants.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ChallengeParticipantSerializer(many=True)})
    def get(self, request, pk):
        try:
            challenge = Challenge.objects.get(pk=pk, deleted_at__isnull=True)
        except Challenge.DoesNotExist:
            return Response({"error": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND)

        can_view = (
            challenge.created_by_id == request.user.id
            or ChallengeParticipant.objects.filter(challenge=challenge, user=request.user).exists()
        )
        if challenge.group_id and not can_view:
            can_view = GroupMembership.objects.filter(
                group_id=challenge.group_id,
                user=request.user,
                is_active=True,
            ).exists()
        if not can_view:
            return Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        participants = challenge.participants.select_related('user').all()

        # Refresh progress for step/water challenges
        if challenge.challenge_type in ('steps', 'water'):
            for p in participants:
                p.refresh_progress()

        serializer = ChallengeParticipantSerializer(participants, many=True)
        return Response(serializer.data)


class RefreshChallengeProgressView(APIView):
    """
    POST: Refresh my progress for a challenge (recomputes from real data).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        participant = ChallengeParticipant.objects.filter(
            user=request.user, challenge_id=pk
        ).select_related('challenge').first()

        if not participant:
            return Response(
                {"error": "You haven't joined this challenge."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progress = participant.refresh_progress()
        return Response({
            'challenge_id': str(pk),
            'cached_progress': progress,
            'target_value': participant.challenge.target_value,
            'progress_percent': participant.progress_percent,
            'is_completed': participant.is_completed,
        })


# ═════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═════════════════════════════════════════════════════════════════════

class NotificationListView(APIView):
    """
    GET: List community notifications for the current user.
    Query params:
      - unread: 'true' to filter only unread notifications
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='unread', type=str, required=False),
        ],
        responses={200: CommunityNotificationSerializer(many=True)},
    )
    def get(self, request):
        qs = CommunityNotification.objects.filter(user=request.user)

        if request.query_params.get('unread') == 'true':
            qs = qs.filter(is_read=False)

        serializer = CommunityNotificationSerializer(qs[:50], many=True)
        return Response(serializer.data)


class MarkNotificationReadView(APIView):
    """
    POST: Mark a single notification as read.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = CommunityNotification.objects.get(
                pk=pk, user=request.user
            )
        except CommunityNotification.DoesNotExist:
            return Response(
                {"error": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.mark_read()
        return Response(CommunityNotificationSerializer(notification).data)


class MarkAllNotificationsReadView(APIView):
    """
    POST: Mark all notifications as read for the current user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()
        count = CommunityNotification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True, read_at=now)
        return Response({"message": f"{count} notifications marked as read."})


class UnreadNotificationCountView(APIView):
    """
    GET: Get count of unread notifications.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = CommunityNotification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response({"unread_count": count})
