"""
Community — Admin configuration
"""
from django.contrib import admin
from .models import (
    CommunityGroup, GroupMembership,
    Challenge, ChallengeParticipant,
    CommunityNotification,
)


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    raw_id_fields = ('user',)
    readonly_fields = ('joined_at',)


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'member_count', 'is_public', 'invite_code', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'created_by__email', 'invite_code')
    raw_id_fields = ('created_by',)
    readonly_fields = ('created_at', 'updated_at', 'invite_code')
    inlines = [GroupMembershipInline]
    fieldsets = (
        ('Group Info', {
            'fields': ('name', 'description', 'icon', 'color')
        }),
        ('Settings', {
            'fields': ('created_by', 'is_public', 'max_members', 'invite_code')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__email', 'group__name')
    raw_id_fields = ('user', 'group')
    readonly_fields = ('joined_at',)


class ChallengeParticipantInline(admin.TabularInline):
    model = ChallengeParticipant
    extra = 0
    raw_id_fields = ('user',)
    readonly_fields = ('joined_at', 'cached_progress', 'last_progress_update')


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'challenge_type', 'status',
        'target_value', 'target_unit',
        'start_date', 'end_date', 'participant_count', 'created_at',
    )
    list_filter = ('challenge_type', 'status', 'start_date', 'is_public')
    search_fields = ('title', 'created_by__email')
    raw_id_fields = ('created_by', 'group')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_date'
    inlines = [ChallengeParticipantInline]
    fieldsets = (
        ('Challenge Info', {
            'fields': ('title', 'description', 'challenge_type', 'icon', 'color')
        }),
        ('Target', {
            'fields': ('target_value', 'target_unit')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Access', {
            'fields': ('created_by', 'group', 'is_public', 'max_participants')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChallengeParticipant)
class ChallengeParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'cached_progress', 'progress_percent', 'joined_at')
    list_filter = ('joined_at',)
    search_fields = ('user__email', 'challenge__title')
    raw_id_fields = ('user', 'challenge')
    readonly_fields = ('joined_at', 'last_progress_update')
    actions = ['refresh_progress']

    @admin.action(description="Refresh progress from real data")
    def refresh_progress(self, request, queryset):
        for participant in queryset:
            participant.refresh_progress()
        self.message_user(request, f"Refreshed progress for {queryset.count()} participants.")


@admin.register(CommunityNotification)
class CommunityNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'user__email', 'message')
    raw_id_fields = ('user', 'related_challenge', 'related_group')
    readonly_fields = ('created_at', 'read_at')
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('References', {
            'fields': ('related_challenge', 'related_group'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
