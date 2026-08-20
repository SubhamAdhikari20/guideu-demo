from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import PaymentTransaction, EscrowLedger


class PaymentTransactionSerializer(serializers.ModelSerializer):
    # The payer is taken from the logged-in user in the view.
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    checkout_payload = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = (
            'id', 'user', 'booking', 'guide_request', 'service_booking', 'amount',
            'currency', 'status', 'gateway', 'gateway_reference', 'mode',
            'checkout_url', 'checkout_payload', 'expires_at', 'verified_at', 'failure_reason', 'created_at'
        )

    def get_checkout_payload(self, obj: PaymentTransaction) -> dict[str, Any] | None:
        if obj.status != PaymentTransaction.Status.PENDING or not obj.gateway_metadata:
            return None
        fields = obj.gateway_metadata.get('form_fields')
        return fields if isinstance(fields, dict) else None
        read_only_fields = (
            'amount', 'currency', 'status', 'gateway_reference', 'mode',
            'checkout_url', 'expires_at', 'verified_at', 'failure_reason', 'created_at'
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        targets = [attrs.get('booking'), attrs.get('guide_request'), attrs.get('service_booking')]
        if sum(bool(target) for target in targets) != 1:
            raise serializers.ValidationError('Choose exactly one booking to pay for.')
        request = self.context['request']
        target = next(target for target in targets if target)
        owner_id = getattr(target, 'tourist_id', None)
        if owner_id != request.user.id and not request.user.is_staff:
            raise serializers.ValidationError('You cannot pay for another user’s booking.')
        return attrs


class EscrowLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscrowLedger
        fields = ('id', 'transaction', 'entry_type', 'amount', 'balance', 'notes', 'created_at')
        read_only_fields = fields


class PaymentCallbackResultSerializer(serializers.Serializer):
    verified = serializers.BooleanField()
