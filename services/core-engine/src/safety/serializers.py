from __future__ import annotations

from rest_framework import serializers

from src.common.sanitize import clean_text

from .models import SosAlert


class SosAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SosAlert
        fields = (
            "id", "user", "latitude", "longitude", "message", "source",
            "status", "resolved_at", "created_at",
        )
        # The owner and lifecycle fields are set server-side, never by the client.
        read_only_fields = ("user", "status", "resolved_at", "created_at")

    def validate_message(self, value: str) -> str:
        return clean_text(value)
