"""
AI — API views for AI health assistant chat.
"""
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from core.mixins import OwnerQuerySetMixin
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    SendMessageSerializer,
    ChatResponseSerializer,
    MessageSerializer,
)
from .providers import SYSTEM_PROMPT, chat as ai_chat

logger = logging.getLogger(__name__)


# ============ Chat endpoint ============

class ChatView(APIView):
    """
    POST /api/v1/ai/chat/
    Send a message to the AI assistant and get a response.
    Optionally pass conversation_id to continue an existing thread.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=SendMessageSerializer, responses={200: ChatResponseSerializer})
    def post(self, request):
        ser = SendMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        user_text = ser.validated_data["message"]
        conv_id = ser.validated_data.get("conversation_id")

        # Get or create conversation
        if conv_id:
            try:
                conversation = Conversation.objects.get(
                    pk=conv_id, user=request.user
                )
            except Conversation.DoesNotExist:
                return Response(
                    {"detail": "Conversation not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # New conversation — title from first message
            title = user_text[:80] + ("…" if len(user_text) > 80 else "")
            conversation = Conversation.objects.create(
                user=request.user, title=title
            )
            # Initialize with the standard greeting
            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content="Hello! I'm your DilCare health assistant. Ask me anything about your health, medications, or wellness tips!",
                model_used="system",
            )

        # Save user message
        user_msg = Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_text,
        )

        # Build message history for the AI (include system prompt)
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        recent_msgs = conversation.messages.order_by("created_at")[:50]
        for m in recent_msgs:
            history.append({"role": m.role, "content": m.content})

        # Call AI provider
        try:
            result = ai_chat(history)
            ai_content = result["content"]
            model_used = result.get("model", "")
            tokens_used = result.get("tokens")
        except Exception as e:
            logger.exception("AI provider error")
            ai_content = (
                "I'm sorry, I'm having trouble connecting right now. "
                "Please try again in a moment. If you need urgent medical help, "
                "please call your doctor or use the SOS feature. 🙏"
            )
            model_used = "fallback"
            tokens_used = None

        # Save AI response
        ai_msg = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=ai_content,
            model_used=model_used,
            tokens_used=tokens_used,
        )

        # Touch conversation updated_at
        conversation.save(update_fields=["updated_at"])

        return Response({
            "conversation_id": str(conversation.id),
            "user_message": MessageSerializer(user_msg).data,
            "ai_message": MessageSerializer(ai_msg).data,
        })


# ============ Conversations ============

class ConversationListView(OwnerQuerySetMixin, generics.ListAPIView):
    """
    GET /api/v1/ai/conversations/
    List all conversations for the user (newest first).
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    owner_field = "user"


class ConversationDetailView(OwnerQuerySetMixin, generics.RetrieveDestroyAPIView):
    """
    GET    /api/v1/ai/conversations/{id}/  — full conversation with all messages
    DELETE /api/v1/ai/conversations/{id}/  — soft-delete conversation
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationDetailSerializer
    permission_classes = [IsAuthenticated]
    owner_field = "user"


#  Conversation History 

class ConversationHistoryView(APIView):
    """
    GET /api/v1/ai/conversations/{id}/messages/
    Returns just the messages for a specific conversation.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MessageSerializer(many=True)})
    def get(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk, user=request.user)
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        messages = conversation.messages.order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)


# ============ Quick Health Check ============

class QuickHealthCheckView(APIView):
    """
    POST /api/v1/ai/quick-check/
    One-shot health question — no conversation history saved.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(request=SendMessageSerializer, responses={200: dict})
    def post(self, request):
        ser = SendMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        user_text = ser.validated_data["message"]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        try:
            result = ai_chat(messages)
            return Response({
                "reply": result["content"],
                "model": result.get("model", ""),
            })
        except Exception as e:
            logger.exception("AI quick-check error")
            return Response({
                "reply": "Sorry, I'm having trouble right now. Please try again later. 🙏",
                "model": "fallback",
            })
