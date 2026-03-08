"""
AI — Serializers.
"""
from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "tokens_used", "model_used", "created_at"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "title", "is_active",
            "last_message", "message_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "title", "created_at", "updated_at"]

    def get_last_message(self, obj) -> str | None:
        msg = obj.messages.order_by("-created_at").first()
        return msg.content[:100] if msg else None

    def get_message_count(self, obj) -> int:
        return obj.messages.count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id", "title", "is_active",
            "messages", "created_at", "updated_at",
        ]


class SendMessageSerializer(serializers.Serializer):
    """Input for sending a message to the AI."""
    message = serializers.CharField(max_length=4000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    """Output after the AI responds."""
    conversation_id = serializers.UUIDField()
    user_message = MessageSerializer()
    ai_message = MessageSerializer()
