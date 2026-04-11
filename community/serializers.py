"""
Community — Serializers for groups, challenges, leaderboard & notifications.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
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

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────
# Group Serializers
# ─────────────────────────────────────────────────────────────────────

class GroupMemberSerializer(serializers.ModelSerializer):
    """Read-only representation of a group member."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = GroupMembership
        fields = [
            'id', 'user_id', 'user_name', 'user_email',
            'role', 'role_display', 'is_active', 'joined_at',
        ]
        read_only_fields = fields


class CommunityGroupSerializer(serializers.ModelSerializer):
    """Full group representation."""
    member_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_member = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = CommunityGroup
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'is_public', 'max_members', 'invite_code',
            'member_count', 'created_by', 'created_by_name',
            'is_member', 'my_role',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'invite_code', 'created_by', 'created_by_name',
            'member_count', 'is_member', 'my_role',
            'created_at', 'updated_at',
        ]

    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.memberships.filter(user=request.user, is_active=True).exists()

    def get_my_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(user=request.user, is_active=True).first()
        return membership.role if membership else None


class CreateGroupSerializer(serializers.ModelSerializer):
    """Serializer for group creation."""
    class Meta:
        model = CommunityGroup
        fields = ['name', 'description', 'icon', 'color', 'is_public', 'max_members']

    def create(self, validated_data):
        user = self.context['request'].user
        group = CommunityGroup.objects.create(created_by=user, **validated_data)
        # Auto-add creator as admin
        GroupMembership.objects.create(user=user, group=group, role='admin')
        return group


class JoinGroupSerializer(serializers.Serializer):
    """Serializer for joining a group via public group_id or private invite code."""
    invite_code = serializers.CharField(max_length=8, required=False, allow_blank=False)
    group_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        invite_code = attrs.get('invite_code')
        group_id = attrs.get('group_id')

        if not invite_code and not group_id:
            raise serializers.ValidationError(
                {"detail": "Either invite_code or group_id is required."}
            )

        if invite_code and group_id:
            raise serializers.ValidationError(
                {"detail": "Provide only one of invite_code or group_id."}
            )

        if invite_code:
            try:
                group = CommunityGroup.objects.get(invite_code=invite_code.upper())
            except CommunityGroup.DoesNotExist:
                raise serializers.ValidationError({"invite_code": "Invalid invite code."})
        else:
            try:
                group = CommunityGroup.objects.get(pk=group_id)
            except CommunityGroup.DoesNotExist:
                raise serializers.ValidationError({"group_id": "Group not found."})

            if not group.is_public:
                raise serializers.ValidationError(
                    {"group_id": "This group is private. Use invite_code to join."}
                )

        user = self.context['request'].user
        if GroupMembership.objects.filter(user=user, group=group, is_active=True).exists():
            raise serializers.ValidationError({"detail": "You are already a member of this group."})

        if group.member_count >= group.max_members:
            raise serializers.ValidationError({"detail": "This group is full."})

        attrs['group'] = group
        return attrs


# ─────────────────────────────────────────────────────────────────────
# Challenge Serializers
# ─────────────────────────────────────────────────────────────────────

class ChallengeParticipantSerializer(serializers.ModelSerializer):
    """Read-only representation of a challenge participant."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = ChallengeParticipant
        fields = [
            'id', 'user_id', 'user_name',
            'cached_progress', 'progress_percent', 'is_completed',
            'joined_at', 'last_progress_update',
        ]
        read_only_fields = fields


class ChallengeSerializer(serializers.ModelSerializer):
    """Full challenge representation."""
    participant_count = serializers.IntegerField(read_only=True)
    type_display = serializers.CharField(source='get_challenge_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, default=None)
    days_remaining = serializers.IntegerField(read_only=True)
    is_joined = serializers.SerializerMethodField()
    joined = serializers.SerializerMethodField()
    my_progress = serializers.SerializerMethodField()
    my_progress_percent = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    name = serializers.CharField(source='title', read_only=True)

    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'description',
            'challenge_type', 'type_display', 'icon', 'color',
            'target_value', 'target_unit',
            'start_date', 'end_date', 'status', 'status_display',
            'days_remaining',
            'created_by', 'created_by_name',
            'group', 'group_name',
            'is_public', 'max_participants', 'participant_count',
            'is_joined', 'joined', 'my_progress', 'my_progress_percent', 'progress',
            'name',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'type_display', 'status_display', 'created_by',
            'created_by_name', 'group_name', 'participant_count',
            'days_remaining', 'is_joined', 'my_progress',
            'my_progress_percent', 'joined', 'progress', 'name',
            'created_at', 'updated_at',
        ]

    def get_is_joined(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.participants.filter(user=request.user).exists()

    def get_my_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        participant = obj.participants.filter(user=request.user).first()
        return participant.cached_progress if participant else 0

    def get_joined(self, obj):
        return self.get_is_joined(obj)

    def get_my_progress_percent(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        participant = obj.participants.filter(user=request.user).first()
        return participant.progress_percent if participant else 0

    def get_progress(self, obj):
        return self.get_my_progress_percent(obj)


class CreateChallengeSerializer(serializers.ModelSerializer):
    """Serializer for creating a challenge."""
    class Meta:
        model = Challenge
        fields = [
            'title', 'description', 'challenge_type', 'icon', 'color',
            'target_value', 'target_unit',
            'start_date', 'end_date',
            'group', 'is_public', 'max_participants',
        ]

    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )
        return data

    def create(self, validated_data):
        from django.utils import timezone
        user = self.context['request'].user
        challenge = Challenge.objects.create(
            created_by=user,
            status='active' if validated_data['start_date'] <= timezone.localdate() else 'upcoming',
            **validated_data,
        )
        # Auto-join the creator
        ChallengeParticipant.objects.create(user=user, challenge=challenge)
        return challenge


# ─────────────────────────────────────────────────────────────────────
# Leaderboard Serializers
# ─────────────────────────────────────────────────────────────────────

class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for a single leaderboard entry."""
    rank = serializers.IntegerField()
    user_id = serializers.UUIDField()
    user_name = serializers.CharField()
    total_steps = serializers.IntegerField()
    avg_steps = serializers.IntegerField()
    days_active = serializers.IntegerField()
    is_self = serializers.BooleanField()


class LeaderboardSerializer(serializers.Serializer):
    """Wrapper for the full leaderboard response."""
    period = serializers.CharField()
    period_label = serializers.CharField()
    entries = LeaderboardEntrySerializer(many=True)
    my_rank = serializers.IntegerField(allow_null=True)
    my_steps = serializers.IntegerField()
    total_participants = serializers.IntegerField()


# ─────────────────────────────────────────────────────────────────────
# Notification Serializers
# ─────────────────────────────────────────────────────────────────────

class CommunityNotificationSerializer(serializers.ModelSerializer):
    """Full notification representation."""
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    challenge_title = serializers.CharField(
        source='related_challenge.title', read_only=True, default=None
    )
    group_name = serializers.CharField(
        source='related_group.name', read_only=True, default=None
    )

    class Meta:
        model = CommunityNotification
        fields = [
            'id', 'notification_type', 'type_display',
            'title', 'message',
            'is_read', 'read_at',
            'challenge_title', 'group_name',
            'created_at',
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────
# Feed Serializers
# ─────────────────────────────────────────────────────────────────────

class CommunityPostCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)

    class Meta:
        model = CommunityPostComment
        fields = ['id', 'user_id', 'user_name', 'content', 'created_at']
        read_only_fields = ['id', 'user_id', 'user_name', 'created_at']


class CommunityPostSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, default=None)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'user_id', 'user_name',
            'group', 'group_name',
            'content', 'post_type', 'milestone_type', 'milestone_value',
            'likes_count', 'comments_count', 'is_liked_by_me',
            'created_at',
        ]
        read_only_fields = [
            'id', 'user_id', 'user_name', 'group_name',
            'post_type', 'milestone_type', 'milestone_value',
            'likes_count', 'comments_count', 'is_liked_by_me',
            'created_at',
        ]

    def get_likes_count(self, obj):
        return obj.reactions.filter(is_active=True).count()

    def get_comments_count(self, obj):
        return obj.comments.filter(is_deleted=False).count()

    def get_is_liked_by_me(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.reactions.filter(user=request.user, is_active=True).exists()


class CreateCommunityPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityPost
        fields = ['group', 'content']

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Content is required.")
        return value.strip()


class CreateCommunityPostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityPostComment
        fields = ['content']

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content is required.")
        return value.strip()


# ─────────────────────────────────────────────────────────────────────
# Group Chat Serializers
# ─────────────────────────────────────────────────────────────────────

class GroupChatMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    mentioned_user_ids = serializers.SerializerMethodField()

    class Meta:
        model = GroupChatMessage
        fields = ['id', 'group', 'user_id', 'user_name', 'content', 'mentioned_user_ids', 'created_at']
        read_only_fields = ['id', 'group', 'user_id', 'user_name', 'mentioned_user_ids', 'created_at']

    def get_mentioned_user_ids(self, obj):
        import re

        email_tokens = re.findall(r'@([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', obj.content or '')
        if not email_tokens:
            return []
        users = User.objects.filter(email__in=email_tokens).values_list('id', flat=True)
        return [str(user_id) for user_id in users]


class CreateGroupChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupChatMessage
        fields = ['content']

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message is required.")
        return value.strip()


class CommunityBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityBadge
        fields = ['id', 'code', 'title', 'description', 'badge_type', 'icon', 'color']
        read_only_fields = fields


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = CommunityBadgeSerializer(read_only=True)
    challenge_id = serializers.UUIDField(source='challenge.id', read_only=True, allow_null=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'challenge_id', 'created_at']
        read_only_fields = fields


class UserCommunityPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCommunityPreference
        fields = [
            'mute_all', 'digest_only',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
        ]


class GroupNotificationPreferenceSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = GroupNotificationPreference
        fields = ['id', 'group', 'group_name', 'is_muted']
        read_only_fields = ['id', 'group_name']


class CommunityModerationReportSerializer(serializers.ModelSerializer):
    reported_by_id = serializers.UUIDField(source='reported_by.id', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)

    class Meta:
        model = CommunityModerationReport
        fields = [
            'id', 'reported_by_id', 'reported_by_name',
            'target_type', 'target_id', 'reason', 'status',
            'created_at',
        ]
        read_only_fields = ['id', 'reported_by_id', 'reported_by_name', 'status', 'created_at']


class CreateCommunityModerationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityModerationReport
        fields = ['target_type', 'target_id', 'reason']

    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Reason is required.')
        return value.strip()


class GroupRoleUpdateSerializer(serializers.Serializer):
    member_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=GroupMembership.ROLE_CHOICES)


class GroupChatUnreadSerializer(serializers.Serializer):
    group_id = serializers.UUIDField()
    unread_count = serializers.IntegerField()
    last_seen_message_id = serializers.UUIDField(allow_null=True)
    has_unread = serializers.BooleanField()
