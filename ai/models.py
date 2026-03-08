"""
AI — Models for chat conversations and messages.
"""
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


class Conversation(SoftDeleteModel):
    """
    A conversation thread between a user and the AI assistant.
    Users can have multiple conversations.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )
    title = models.CharField(
        max_length=200, blank=True,
        help_text="Auto-generated from first user message",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "AI Conversation"
        verbose_name_plural = "AI Conversations"

    def __str__(self):
        return f"{self.user} — {self.title or 'Untitled'}"


class Message(models.Model):
    """
    A single message in an AI conversation.
    """
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]
    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional metadata
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"
