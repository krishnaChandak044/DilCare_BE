from django.urls import path
from . import views

urlpatterns = [
    # Chat
    path("chat/", views.ChatView.as_view(), name="ai-chat"),
    path("quick-check/", views.QuickHealthCheckView.as_view(), name="ai-quick-check"),

    # Conversations
    path("conversations/", views.ConversationListView.as_view(), name="ai-conversations"),
    path("conversations/<uuid:pk>/", views.ConversationDetailView.as_view(), name="ai-conversation-detail"),
    path("conversations/<uuid:pk>/messages/", views.ConversationHistoryView.as_view(), name="ai-conversation-messages"),
]
