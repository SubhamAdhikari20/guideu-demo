from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import TrekkingPermit


class TrekkingPermitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrekkingPermit
        fields = ('id', 'applicant', 'permit_type', 'applied_date', 'status', 'documents', 'route_bounds', 'admin_notes')
        read_only_fields = ('applicant', 'status', 'admin_notes')

    def validate_documents(self, value: Any) -> Any:
        if not value:
            raise serializers.ValidationError('At least one document is required to apply for a permit.')
        return value
