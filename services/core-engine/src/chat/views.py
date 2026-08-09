"""REST surface for chat history.

Live messages travel over the Socket.IO ``real-time-engine``; these endpoints
store and read the durable history. The realtime engine calls
``POST /chat/messages/`` (as the sending user) to persist each delivered message,
and the app reads ``GET /chat/messages/?room=...`` to load the backlog.
"""
from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatMessage, ChatThread
from .serializers import ChatMessageSerializer, ChatThreadSerializer, SendMessageSerializer
from .services import get_or_create_thread


class ChatThreadViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """The chat inbox: threads the current user is part of, newest first."""

    serializer_class = ChatThreadSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            ChatThread.objects.filter(participants=self.request.user)
            .prefetch_related("messages")
            .distinct()
        )


class ChatMessageViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None  # chat history is read whole, oldest-first

    def _thread_for(self, room: str) -> ChatThread:
        thread = get_or_create_thread(room)
        if not thread.participants.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("You are not a participant in this conversation.")
        return thread

    @extend_schema(parameters=[OpenApiParameter("room", str, required=True)])
    def list(self, request, *args, **kwargs):
        room = request.query_params.get("room")
        if not room:
            raise ValidationError({"room": "This query parameter is required."})
        thread = self._thread_for(room)
        # Reading the thread clears unread messages sent by the other person.
        thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        messages = thread.messages.select_related("sender").all()
        return Response(ChatMessageSerializer(messages, many=True).data)

    @extend_schema(request=SendMessageSerializer, responses=ChatMessageSerializer)
    def create(self, request, *args, **kwargs):
        payload = SendMessageSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        thread = self._thread_for(payload.validated_data["room"])
        message = ChatMessage.objects.create(
            thread=thread, sender=request.user, body=payload.validated_data["body"]
        )
        thread.save(update_fields=["updated_at"])
        return Response(ChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)
