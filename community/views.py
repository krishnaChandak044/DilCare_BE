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
    CommunityPost, CommunityPostReaction, CommunityPostComment,
    GroupChatMessage,
    CommunityBadge, UserBadge,
    UserCommunityPreference, GroupNotificationPreference,
    CommunityModerationReport, GroupChatReadState,
)
from .serializers import (
    CommunityGroupSerializer, CreateGroupSerializer, JoinGroupSerializer,
    GroupMemberSerializer,
    ChallengeSerializer, CreateChallengeSerializer, ChallengeParticipantSerializer,
    LeaderboardSerializer,
    CommunityNotificationSerializer,
    CommunityPostSerializer, CreateCommunityPostSerializer,
    CommunityPostCommentSerializer, CreateCommunityPostCommentSerializer,
    GroupChatMessageSerializer, CreateGroupChatMessageSerializer,
    UserBadgeSerializer,
    UserCommunityPreferenceSerializer, GroupNotificationPreferenceSerializer,
    CommunityModerationReportSerializer, CreateCommunityModerationReportSerializer,
    GroupRoleUpdateSerializer, GroupChatUnreadSerializer,
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


def should_send_notification(user, group=None):
    preference = UserCommunityPreference.objects.filter(user=user).first()
    if preference and preference.mute_all:
        return False

    if preference and preference.quiet_hours_enabled and preference.quiet_hours_start and preference.quiet_hours_end:
        current_time = timezone.localtime().time()
        start = preference.quiet_hours_start
        end = preference.quiet_hours_end
        if start <= end:
            if start <= current_time <= end:
                return False
        else:
            if current_time >= start or current_time <= end:
                return False

    if group is not None:
        group_pref = GroupNotificationPreference.objects.filter(user=user, group=group).first()
        if group_pref and group_pref.is_muted:
            return False

    return True


def create_community_notification(*, user, notification_type, title, message='', related_group=None, related_challenge=None):
    if not should_send_notification(user, group=related_group):
        return None

    return CommunityNotification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_group=related_group,
        related_challenge=related_challenge,
    )


def award_badge(user, badge_code, challenge=None):
    badge, _ = CommunityBadge.objects.get_or_create(
        code=badge_code,
        defaults={
            'title': badge_code.replace('_', ' ').title(),
            'description': 'Community achievement unlocked.',
            'badge_type': 'milestone',
            'icon': 'trophy',
            'color': '#F59E0B',
        },
    )

    award, created = UserBadge.objects.get_or_create(
        user=user,
        badge=badge,
        challenge=challenge,
    )
    return award if created else None


def generate_user_milestone_posts(user):
    created_posts = []
    today = timezone.localdate()

    from steps.models import DailyStepLog
    from water.models import DailyWaterLog
    from medicine.models import MedicineIntake

    milestones = []

    step_today = DailyStepLog.objects.filter(user=user, date=today).first()
    if step_today and step_today.total_steps:
        for threshold in [5000, 10000, 20000]:
            if step_today.total_steps >= threshold:
                milestones.append(('steps', threshold, f"I reached {threshold:,} steps today! 🚶"))

    water_today = DailyWaterLog.objects.filter(user=user, date=today).first()
    if water_today and water_today.glasses:
        for threshold in [4, 8, 12]:
            if water_today.glasses >= threshold:
                milestones.append(('water', threshold, f"Hydration milestone: {threshold} glasses today! 💧"))

    taken_today = MedicineIntake.objects.filter(
        medicine__user=user,
        scheduled_date=today,
        status='taken',
    ).count()
    if taken_today >= 1:
        milestones.append(('medicine', taken_today, f"Completed {taken_today} medicine doses today ✅"))

    for milestone_type, milestone_value, content in milestones:
        exists = CommunityPost.objects.filter(
            user=user,
            post_type='milestone',
            milestone_type=milestone_type,
            milestone_value=milestone_value,
            created_at__date=today,
            is_deleted=False,
        ).exists()
        if exists:
            continue

        post = CommunityPost.objects.create(
            user=user,
            content=content,
            post_type='milestone',
            milestone_type=milestone_type,
            milestone_value=milestone_value,
        )
        created_posts.append(post)

        badge_code = f"milestone_{milestone_type}_{milestone_value}"
        award = award_badge(user, badge_code)
        if award:
            create_community_notification(
                user=user,
                notification_type='achievement',
                title='New badge unlocked!',
                message=f"You earned the {award.badge.title} badge.",
            )

    return created_posts


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


class GroupRoleUpdateView(APIView):
    """
    POST: Update a member role in a group (admin only).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=GroupRoleUpdateSerializer, responses={200: GroupMemberSerializer})
    def post(self, request, pk):
        admin_membership = GroupMembership.objects.filter(
            user=request.user, group_id=pk, is_active=True, role='admin'
        ).first()
        if not admin_membership:
            return Response({'error': 'Only admins can update roles.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = GroupRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = GroupMembership.objects.filter(
            group_id=pk,
            user_id=serializer.validated_data['member_id'],
            is_active=True,
        ).select_related('user').first()
        if not membership:
            return Response({'error': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)

        membership.role = serializer.validated_data['role']
        membership.save(update_fields=['role', 'updated_at'])

        return Response(GroupMemberSerializer(membership).data)


class GroupMemberRemoveView(APIView):
    """
    POST: Remove a member from a group (admin/moderator, or self-leave).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, member_id):
        actor_membership = GroupMembership.objects.filter(
            group_id=pk, user=request.user, is_active=True,
        ).first()
        if not actor_membership:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        target_membership = GroupMembership.objects.filter(
            group_id=pk, user_id=member_id, is_active=True,
        ).first()
        if not target_membership:
            return Response({'error': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)

        can_remove = (
            request.user.id == target_membership.user_id
            or actor_membership.role == 'admin'
            or (actor_membership.role == 'moderator' and target_membership.role == 'member')
        )
        if not can_remove:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        if target_membership.role == 'admin':
            remaining_admins = GroupMembership.objects.filter(
                group_id=pk, role='admin', is_active=True,
            ).exclude(user_id=target_membership.user_id).count()
            if remaining_admins == 0:
                return Response(
                    {'error': 'Cannot remove the last admin from group.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        target_membership.is_active = False
        target_membership.save(update_fields=['is_active', 'updated_at'])
        return Response({'message': 'Member removed successfully.'})


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
        group = serializer.validated_data['group']

        membership, created = GroupMembership.objects.get_or_create(
            user=request.user, group=group,
            defaults={'role': 'member'}
        )
        if not created and not membership.is_active:
            membership.is_active = True
            membership.save(update_fields=['is_active'])

        # Send notification to group admin
        create_community_notification(
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

        if challenge.status == 'active':
            award_badge(request.user, 'challenge_joiner')

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
        if participant.is_completed:
            award = award_badge(request.user, 'challenge_complete', challenge=participant.challenge)
            if award:
                create_community_notification(
                    user=request.user,
                    notification_type='challenge_completed',
                    title='Challenge completed!',
                    message=f"You completed {participant.challenge.title}.",
                    related_challenge=participant.challenge,
                )

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


class UserCommunityPreferenceView(APIView):
    """
    GET/PATCH: View or update current user's smart notification preferences.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserCommunityPreferenceSerializer})
    def get(self, request):
        preference, _ = UserCommunityPreference.objects.get_or_create(user=request.user)
        return Response(UserCommunityPreferenceSerializer(preference).data)

    @extend_schema(request=UserCommunityPreferenceSerializer, responses={200: UserCommunityPreferenceSerializer})
    def patch(self, request):
        preference, _ = UserCommunityPreference.objects.get_or_create(user=request.user)
        serializer = UserCommunityPreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GroupNotificationPreferenceView(APIView):
    """
    GET: List my group notification preferences.
    POST: Upsert mute setting for a group.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: GroupNotificationPreferenceSerializer(many=True)})
    def get(self, request):
        prefs = GroupNotificationPreference.objects.filter(user=request.user).select_related('group')
        return Response(GroupNotificationPreferenceSerializer(prefs, many=True).data)

    @extend_schema(
        request=GroupNotificationPreferenceSerializer,
        responses={200: GroupNotificationPreferenceSerializer},
    )
    def post(self, request):
        group_id = request.data.get('group')
        is_muted = bool(request.data.get('is_muted', False))
        membership_exists = GroupMembership.objects.filter(
            user=request.user, group_id=group_id, is_active=True,
        ).exists()
        if not membership_exists:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        pref, _ = GroupNotificationPreference.objects.get_or_create(
            user=request.user,
            group_id=group_id,
            defaults={'is_muted': is_muted},
        )
        pref.is_muted = is_muted
        pref.save(update_fields=['is_muted', 'updated_at'])
        return Response(GroupNotificationPreferenceSerializer(pref).data)


class UserBadgeListView(APIView):
    """
    GET: List badges awarded to current user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserBadgeSerializer(many=True)})
    def get(self, request):
        badges = UserBadge.objects.filter(user=request.user).select_related('badge', 'challenge')[:100]
        return Response(UserBadgeSerializer(badges, many=True).data)


class MilestoneSyncView(APIView):
    """
    POST: Generate today's milestone feed posts from steps/water/medicine logs.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        created_posts = generate_user_milestone_posts(request.user)
        return Response({
            'created_count': len(created_posts),
            'created_post_ids': [str(post.id) for post in created_posts],
        })


class ModerationReportListCreateView(APIView):
    """
    GET: List my moderation reports.
    POST: Submit a moderation report.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CommunityModerationReportSerializer(many=True)})
    def get(self, request):
        reports = CommunityModerationReport.objects.filter(reported_by=request.user)[:100]
        return Response(CommunityModerationReportSerializer(reports, many=True).data)

    @extend_schema(request=CreateCommunityModerationReportSerializer, responses={201: CommunityModerationReportSerializer})
    def post(self, request):
        serializer = CreateCommunityModerationReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = CommunityModerationReport.objects.create(
            reported_by=request.user,
            **serializer.validated_data,
        )
        return Response(CommunityModerationReportSerializer(report).data, status=status.HTTP_201_CREATED)


# ═════════════════════════════════════════════════════════════════════
# FEED
# ═════════════════════════════════════════════════════════════════════

class FeedListCreateView(APIView):
    """
    GET: List feed posts (global + groups user belongs to).
    POST: Create a new feed post.
    Query params:
      - group: UUID to filter posts by group
            - sort: latest | trending
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='group', type=str, required=False),
            OpenApiParameter(name='sort', type=str, required=False, enum=['latest', 'trending']),
        ],
        responses={200: CommunityPostSerializer(many=True)},
    )
    def get(self, request):
        my_group_ids = GroupMembership.objects.filter(
            user=request.user, is_active=True
        ).values_list('group_id', flat=True)

        qs = CommunityPost.objects.filter(
            Q(group__isnull=True) | Q(group_id__in=my_group_ids)
        ).select_related('user', 'group')

        group_id = request.query_params.get('group')
        if group_id:
            qs = qs.filter(group_id=group_id)

        sort_by = request.query_params.get('sort', 'latest')
        if sort_by == 'trending':
            qs = qs.annotate(
                active_like_count=Count('reactions', filter=Q(reactions__is_active=True), distinct=True),
                active_comment_count=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
            ).order_by('-active_like_count', '-active_comment_count', '-created_at')
        else:
            qs = qs.order_by('-created_at')

        serializer = CommunityPostSerializer(qs[:50], many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(request=CreateCommunityPostSerializer, responses={201: CommunityPostSerializer})
    def post(self, request):
        serializer = CreateCommunityPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data.get('group')

        if group:
            is_member = GroupMembership.objects.filter(
                user=request.user, group=group, is_active=True
            ).exists()
            if not is_member:
                return Response(
                    {"error": "You must be a member of the group to post."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        post = CommunityPost.objects.create(
            user=request.user,
            group=group,
            content=serializer.validated_data['content'],
        )
        return Response(
            CommunityPostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class FeedLikeToggleView(APIView):
    """POST: Toggle like for a feed post."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = CommunityPost.objects.select_related('group').get(pk=pk)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if post.group_id:
            is_member = GroupMembership.objects.filter(
                user=request.user, group_id=post.group_id, is_active=True
            ).exists()
            if not is_member:
                return Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        reaction, created = CommunityPostReaction.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={'is_active': True},
        )
        if created:
            liked = True
        elif not reaction.is_active:
            reaction.is_active = True
            reaction.save(update_fields=['is_active', 'updated_at'])
            liked = True
        else:
            reaction.is_active = False
            reaction.save(update_fields=['is_active', 'updated_at'])
            liked = False

        return Response({
            'post_id': str(post.id),
            'liked': liked,
            'likes_count': post.reactions.filter(is_active=True).count(),
        })


class FeedCommentListCreateView(APIView):
    """
    GET: List comments for a post.
    POST: Add a comment to a post.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CommunityPostCommentSerializer(many=True)})
    def get(self, request, pk):
        try:
            post = CommunityPost.objects.select_related('group').get(pk=pk)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if post.group_id:
            is_member = GroupMembership.objects.filter(
                user=request.user, group_id=post.group_id, is_active=True
            ).exists()
            if not is_member:
                return Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        comments = post.comments.select_related('user').filter(is_deleted=False)
        serializer = CommunityPostCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @extend_schema(request=CreateCommunityPostCommentSerializer, responses={201: CommunityPostCommentSerializer})
    def post(self, request, pk):
        try:
            post = CommunityPost.objects.select_related('group').get(pk=pk)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if post.group_id:
            is_member = GroupMembership.objects.filter(
                user=request.user, group_id=post.group_id, is_active=True
            ).exists()
            if not is_member:
                return Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateCommunityPostCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = CommunityPostComment.objects.create(
            user=request.user,
            post=post,
            content=serializer.validated_data['content'],
        )
        return Response(
            CommunityPostCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )


# ═════════════════════════════════════════════════════════════════════
# GROUP CHAT
# ═════════════════════════════════════════════════════════════════════

class GroupChatView(APIView):
    """
    GET: List group chat messages.
    POST: Send a group chat message.
    """
    permission_classes = [IsAuthenticated]

    def _get_group_if_member(self, user, group_id):
        try:
            group = CommunityGroup.objects.get(pk=group_id, deleted_at__isnull=True)
        except CommunityGroup.DoesNotExist:
            return None, Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        is_member = GroupMembership.objects.filter(
            user=user, group=group, is_active=True
        ).exists()
        if not is_member:
            return None, Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        return group, None

    @extend_schema(responses={200: GroupChatMessageSerializer(many=True)})
    def get(self, request, pk):
        group, error = self._get_group_if_member(request.user, pk)
        if error:
            return error

        messages = GroupChatMessage.objects.filter(group=group).select_related('user').order_by('created_at')[:100]
        last_message = messages.last()
        if last_message:
            GroupChatReadState.objects.update_or_create(
                user=request.user,
                group=group,
                defaults={
                    'last_seen_message': last_message,
                    'last_seen_at': timezone.now(),
                },
            )
        serializer = GroupChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @extend_schema(request=CreateGroupChatMessageSerializer, responses={201: GroupChatMessageSerializer})
    def post(self, request, pk):
        group, error = self._get_group_if_member(request.user, pk)
        if error:
            return error

        serializer = CreateGroupChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = GroupChatMessage.objects.create(
            group=group,
            user=request.user,
            content=serializer.validated_data['content'],
        )

        GroupChatReadState.objects.update_or_create(
            user=request.user,
            group=group,
            defaults={
                'last_seen_message': message,
                'last_seen_at': timezone.now(),
            },
        )

        import re

        mentions = re.findall(r'@([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', message.content or '')
        if mentions:
            mentioned_users = User.objects.filter(email__in=mentions).exclude(id=request.user.id)
            member_user_ids = set(
                GroupMembership.objects.filter(group=group, is_active=True).values_list('user_id', flat=True)
            )
            for target_user in mentioned_users:
                if target_user.id in member_user_ids:
                    create_community_notification(
                        user=target_user,
                        notification_type='general',
                        title='You were mentioned in group chat',
                        message=f"{request.user.get_full_name() or request.user.email}: {message.content[:120]}",
                        related_group=group,
                    )

        return Response(GroupChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class GroupChatUnreadView(APIView):
    """
    GET: Unread chat counts for all groups of current user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: GroupChatUnreadSerializer(many=True)})
    def get(self, request):
        memberships = GroupMembership.objects.filter(user=request.user, is_active=True).values_list('group_id', flat=True)
        payload = []
        for group_id in memberships:
            last_message = GroupChatMessage.objects.filter(group_id=group_id, is_deleted=False).order_by('-created_at').first()
            read_state = GroupChatReadState.objects.filter(user=request.user, group_id=group_id).first()
            if not last_message:
                payload.append({
                    'group_id': group_id,
                    'unread_count': 0,
                    'last_seen_message_id': None,
                    'has_unread': False,
                })
                continue

            unread_qs = GroupChatMessage.objects.filter(group_id=group_id, is_deleted=False)
            if read_state and read_state.last_seen_message_id:
                unread_qs = unread_qs.filter(created_at__gt=read_state.last_seen_message.created_at)

            unread_count = unread_qs.count()
            payload.append({
                'group_id': group_id,
                'unread_count': unread_count,
                'last_seen_message_id': str(read_state.last_seen_message_id) if read_state and read_state.last_seen_message_id else None,
                'has_unread': unread_count > 0,
            })

        serializer = GroupChatUnreadSerializer(payload, many=True)
        return Response(serializer.data)
