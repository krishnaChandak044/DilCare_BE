"""
Community — Models for groups, challenges, leaderboards & notifications.

Integrates with the Steps app (DailyStepLog) for step-based leaderboards
and challenge progress tracking.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import SoftDeleteModel, TimeStampedModel

User = get_user_model()


# Community Groups

class CommunityGroup(SoftDeleteModel):
    """
    A group of users who can compete on leaderboards
    and participate in challenges together.
    """
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(
        max_length=30, default='people',
        help_text="Ionicons icon name for the group"
    )
    color = models.CharField(
        max_length=7, default='#6366F1',
        help_text="Hex color for the group badge"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_groups'
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Public groups are discoverable by all users"
    )
    max_members = models.PositiveIntegerField(default=50)
    invite_code = models.CharField(
        max_length=8, unique=True, blank=True, null=True,
        help_text="Short code for private group invites"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()

    def save(self, *args, **kwargs):
        if not self.invite_code:
            import secrets
            self.invite_code = secrets.token_urlsafe(6)[:8].upper()
        super().save(*args, **kwargs)


class GroupMembership(SoftDeleteModel):
    """
    Through-table for user membership in a community group.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    group = models.ForeignKey(
        CommunityGroup, on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} → {self.group.name} ({self.role})"


# ─────────────────────────────────────────────────────────────────────
# Challenges
# ─────────────────────────────────────────────────────────────────────

class Challenge(SoftDeleteModel):
    """
    A community challenge that users can join and track progress.
    Supports both step-based and custom target challenges.
    """
    TYPE_CHOICES = [
        ('steps', 'Steps Challenge'),
        ('water', 'Water Challenge'),
        ('medicine', 'Medicine Adherence'),
        ('custom', 'Custom Challenge'),
    ]
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    challenge_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='steps')
    icon = models.CharField(max_length=30, default='footsteps')
    color = models.CharField(max_length=7, default='#F97316')

    # Target & progress
    target_value = models.PositiveIntegerField(
        help_text="Target value (e.g., 50000 steps, 56 glasses of water)"
    )
    target_unit = models.CharField(
        max_length=20, default='steps',
        help_text="e.g., steps, glasses, days"
    )

    # Duration
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='upcoming')

    # Ownership
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_challenges'
    )
    group = models.ForeignKey(
        CommunityGroup, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='challenges',
        help_text="Optional: restrict challenge to a group"
    )
    is_public = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', '-start_date']),
            models.Index(fields=['challenge_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_challenge_type_display()})"

    @property
    def participant_count(self):
        return self.participants.count()

    @property
    def is_active(self):
        today = timezone.localdate()
        return self.start_date <= today <= self.end_date and self.status == 'active'

    @property
    def days_remaining(self):
        today = timezone.localdate()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    def auto_update_status(self):
        """Auto-update status based on dates."""
        today = timezone.localdate()
        if self.status == 'upcoming' and today >= self.start_date:
            self.status = 'active'
            self.save(update_fields=['status'])
        elif self.status == 'active' and today > self.end_date:
            self.status = 'completed'
            self.save(update_fields=['status'])


class ChallengeParticipant(SoftDeleteModel):
    """
    A user's participation in a challenge.
    Progress is computed from real app data (steps, water, etc.)
    but can be cached for performance.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='challenge_participations'
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE,
        related_name='participants'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    # Cached progress (updated periodically or on request)
    cached_progress = models.PositiveIntegerField(default=0)
    last_progress_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'challenge']
        ordering = ['-cached_progress']

    def __str__(self):
        return f"{self.user.email} → {self.challenge.title}"

    @property
    def progress_percent(self):
        if self.challenge.target_value == 0:
            return 100
        return min(100, round(
            (self.cached_progress / self.challenge.target_value) * 100
        ))

    @property
    def is_completed(self):
        return self.cached_progress >= self.challenge.target_value

    def compute_step_progress(self):
        """
        Compute real progress from DailyStepLog for step challenges.
        """
        from steps.models import DailyStepLog
        from django.db.models import Sum

        if self.challenge.challenge_type != 'steps':
            return self.cached_progress

        total = DailyStepLog.objects.filter(
            user=self.user,
            date__gte=self.challenge.start_date,
            date__lte=min(self.challenge.end_date, timezone.localdate()),
        ).aggregate(total=Sum('total_steps'))['total'] or 0

        self.cached_progress = total
        self.last_progress_update = timezone.now()
        self.save(update_fields=['cached_progress', 'last_progress_update'])
        return total

    def compute_water_progress(self):
        """
        Compute real progress from DailyWaterLog for water challenges.
        """
        from water.models import DailyWaterLog
        from django.db.models import Sum

        if self.challenge.challenge_type != 'water':
            return self.cached_progress

        total = DailyWaterLog.objects.filter(
            user=self.user,
            date__gte=self.challenge.start_date,
            date__lte=min(self.challenge.end_date, timezone.localdate()),
        ).aggregate(total=Sum('glasses'))['total'] or 0

        self.cached_progress = total
        self.last_progress_update = timezone.now()
        self.save(update_fields=['cached_progress', 'last_progress_update'])
        return total

    def refresh_progress(self):
        """Refresh cached progress based on challenge type."""
        if self.challenge.challenge_type == 'steps':
            return self.compute_step_progress()
        elif self.challenge.challenge_type == 'water':
            return self.compute_water_progress()
        return self.cached_progress


# ─────────────────────────────────────────────────────────────────────
# Community Notifications
# ─────────────────────────────────────────────────────────────────────

class CommunityNotification(SoftDeleteModel):
    """
    In-app notifications for community events.
    """
    TYPE_CHOICES = [
        ('challenge_invite', 'Challenge Invitation'),
        ('challenge_started', 'Challenge Started'),
        ('challenge_completed', 'Challenge Completed'),
        ('challenge_milestone', 'Challenge Milestone'),
        ('group_invite', 'Group Invitation'),
        ('group_joined', 'Member Joined Group'),
        ('leaderboard_rank', 'Leaderboard Rank Change'),
        ('achievement', 'Achievement Unlocked'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='community_notifications'
    )
    notification_type = models.CharField(max_length=25, choices=TYPE_CHOICES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True, default='')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Optional references
    related_challenge = models.ForeignKey(
        Challenge, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )
    related_group = models.ForeignKey(
        CommunityGroup, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.email} — {self.title}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# Community Feed

class CommunityPost(SoftDeleteModel):
    """A community feed post. Optionally scoped to a group."""
    POST_TYPE_CHOICES = [
        ('text', 'Text'),
        ('milestone', 'Milestone'),
    ]
    MILESTONE_TYPE_CHOICES = [
        ('steps', 'Steps'),
        ('water', 'Water'),
        ('medicine', 'Medicine'),
        ('streak', 'Streak'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='community_posts'
    )
    group = models.ForeignKey(
        CommunityGroup, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posts'
    )
    content = models.TextField(max_length=1000)
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='text')
    milestone_type = models.CharField(
        max_length=20, choices=MILESTONE_TYPE_CHOICES,
        null=True, blank=True,
    )
    milestone_value = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['user', 'post_type', '-created_at']),
        ]

    def __str__(self):
        scope = self.group.name if self.group else 'Global'
        return f"{self.user.email} · {scope}"


class CommunityPostReaction(TimeStampedModel):
    """Like reaction for a post with toggle support."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='community_post_reactions'
    )
    post = models.ForeignKey(
        CommunityPost, on_delete=models.CASCADE,
        related_name='reactions'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} → {self.post_id} ({'active' if self.is_active else 'inactive'})"


class CommunityPostComment(SoftDeleteModel):
    """Comment on a community post."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='community_post_comments'
    )
    post = models.ForeignKey(
        CommunityPost, on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(max_length=500)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} comment on {self.post_id}"


# ─────────────────────────────────────────────────────────────────────
# Group Chat
# ─────────────────────────────────────────────────────────────────────

class GroupChatMessage(SoftDeleteModel):
    """Simple persistent group chat message."""
    group = models.ForeignKey(
        CommunityGroup, on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='group_chat_messages'
    )
    content = models.TextField(max_length=1000)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
        ]

    def __str__(self):
        return f"{self.group.name} · {self.user.email}"


class UserCommunityPreference(SoftDeleteModel):
    """User-level smart notification preferences for community updates."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='community_preference'
    )
    mute_all = models.BooleanField(default=False)
    digest_only = models.BooleanField(default=False)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prefs: {self.user.email}"


class GroupNotificationPreference(SoftDeleteModel):
    """Per-group notification muting controls."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='group_notification_preferences'
    )
    group = models.ForeignKey(
        CommunityGroup, on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} mute={self.is_muted} {self.group.name}"


class CommunityBadge(SoftDeleteModel):
    """Badge catalog for community achievements."""
    TYPE_CHOICES = [
        ('challenge_complete', 'Challenge Completion'),
        ('challenge_winner', 'Challenge Winner'),
        ('streak', 'Streak Badge'),
        ('milestone', 'Milestone Badge'),
    ]

    code = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True, default='')
    badge_type = models.CharField(max_length=25, choices=TYPE_CHOICES, default='milestone')
    icon = models.CharField(max_length=30, default='trophy')
    color = models.CharField(max_length=7, default='#F59E0B')

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class UserBadge(SoftDeleteModel):
    """Awarded badges for users."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='community_badges'
    )
    badge = models.ForeignKey(
        CommunityBadge, on_delete=models.CASCADE,
        related_name='awards'
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='awarded_badges'
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'badge', 'challenge']

    def __str__(self):
        return f"{self.user.email} → {self.badge.code}"


class CommunityModerationReport(SoftDeleteModel):
    """Member-submitted moderation reports for posts/comments/chat."""
    TARGET_CHOICES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('chat_message', 'Chat Message'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    reported_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='community_reports'
    )
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_id = models.UUIDField()
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.target_type}:{self.target_id} ({self.status})"


class GroupChatReadState(SoftDeleteModel):
    """Tracks last seen chat message per user/group for unread counts."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='group_chat_read_states'
    )
    group = models.ForeignKey(
        CommunityGroup, on_delete=models.CASCADE,
        related_name='chat_read_states'
    )
    last_seen_message = models.ForeignKey(
        GroupChatMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seen_by_states',
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-updated_at']

    def __str__(self):
        return f"ReadState: {self.user.email} @ {self.group.name}"
