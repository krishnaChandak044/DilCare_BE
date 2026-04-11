"""
Family — Admin configuration
"""
from django.contrib import admin
from .models import Family, FamilyMembership, FamilyLink


class FamilyMembershipInline(admin.TabularInline):
    model = FamilyMembership
    extra = 0
    readonly_fields = ("joined_at",)
    raw_id_fields = ("user",)


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "invite_code", "member_count", "created_by", "created_at")
    search_fields = ("name", "invite_code", "created_by__email")
    readonly_fields = ("invite_code", "created_at", "updated_at")
    inlines = [FamilyMembershipInline]

    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = "Members"


@admin.register(FamilyMembership)
class FamilyMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "family", "role", "nickname", "joined_at")
    list_filter = ("role",)
    search_fields = ("user__email", "family__name")
    raw_id_fields = ("user", "family")


# Keep old model registered but marked as deprecated
@admin.register(FamilyLink)
class FamilyLinkAdmin(admin.ModelAdmin):
    list_display = ("child", "parent", "relationship", "is_active", "linked_at")
    list_filter = ("relationship", "is_active")
    search_fields = ("child__email", "parent__email")

    class Meta:
        verbose_name = "[DEPRECATED] Family Link"
