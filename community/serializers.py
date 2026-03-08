"""
Community — Serializers for groups, challenges, leaderboard & notifications.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CommunityGroup, GroupMembership,
    Challenge, ChallengeParticipant,
    CommunityNotification,
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
    """Serializer for joining a group via invite code."""
    invite_code = serializers.CharField(max_length=8)

    def validate_invite_code(self, value):
        try:
            group = CommunityGroup.objects.get(invite_code=value.upper())
        except CommunityGroup.DoesNotExist:
            raise serializers.ValidationError("Invalid invite code.")

        user = self.context['request'].user
        if GroupMembership.objects.filter(user=user, group=group, is_active=True).exists():
            raise serializers.ValidationError("You are already a member of this group.")

        if group.member_count >= group.max_members:
            raise serializers.ValidationError("This group is full.")

        self.group = group
        return value


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
    my_progress = serializers.SerializerMethodField()
    my_progress_percent = serializers.SerializerMethodField()

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
            'is_joined', 'my_progress', 'my_progress_percent',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'type_display', 'status_display', 'created_by',
            'created_by_name', 'group_name', 'participant_count',
            'days_remaining', 'is_joined', 'my_progress',
            'my_progress_percent', 'created_at', 'updated_at',
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

    def get_my_progress_percent(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        participant = obj.participants.filter(user=request.user).first()
        return participant.progress_percent if participant else 0


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
