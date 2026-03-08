from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "model_used", "tokens_used", "created_at")
    ordering = ("created_at",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("short_content", "role", "conversation", "model_used", "created_at")
    list_filter = ("role", "model_used", "created_at")
    search_fields = ("content",)
    readonly_fields = ("created_at",)

    @admin.display(description="Content")
    def short_content(self, obj):
        return obj.content[:80] + "…" if len(obj.content) > 80 else obj.content
