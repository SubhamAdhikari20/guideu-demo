from __future__ import annotations

from rest_framework import serializers

from src.common.sanitize import clean_text

from .models import ChatMessage, ChatThread


class ChatMessageSerializer(serializers.ModelSerializer):
    room = serializers.CharField(source="thread.room", read_only=True)
    sender_name = serializers.CharField(source="sender.username", read_only=True, default="")

    class Meta:
        model = ChatMessage
        fields = ("id", "room", "sender", "sender_name", "body", "is_read", "created_at")
        read_only_fields = ("id", "room", "sender", "sender_name", "is_read", "created_at")


class SendMessageSerializer(serializers.Serializer):
    """Input for posting a message: the room to post into and the text."""

    room = serializers.CharField(max_length=64)
    body = serializers.CharField(max_length=4000, trim_whitespace=True)

    def validate_body(self, value: str) -> str:
        cleaned = clean_text(value)
        if not cleaned:
            raise serializers.ValidationError("Message cannot be empty.")
        return cleaned


class ChatThreadSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ("id", "room", "last_message", "unread_count", "updated_at")

    def get_last_message(self, obj) -> dict | None:
        msg = obj.messages.order_by("-created_at").first()
        return ChatMessageSerializer(msg).data if msg else None

    def get_unread_count(self, obj) -> int:
        user = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()
