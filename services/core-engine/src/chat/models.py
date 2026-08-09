"""Persisted chat history for the guide ↔ tourist conversation.

The live delivery is handled by the ``real-time-engine`` (Socket.IO); this app is
the durable record so the app can show past messages and unread counts. A thread
is keyed by the same room string the socket uses, e.g. ``booking:42``.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from src.common.models import TimeStampedModel


class ChatThread(TimeStampedModel):
    room = models.CharField(max_length=64, unique=True, db_index=True, help_text="Socket room, e.g. booking:42")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="chat_threads")

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.room


class ChatMessage(TimeStampedModel):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_messages"
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["thread", "created_at"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.sender_id} @ {self.thread.room}: {self.body[:30]}"
