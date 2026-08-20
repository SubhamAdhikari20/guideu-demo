from __future__ import annotations

from django.conf import settings
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction, EscrowLedger
from .serializers import EscrowLedgerSerializer, PaymentCallbackResultSerializer, PaymentTransactionSerializer
from .services import initiate, mark_success, payable_amount, verify_esewa_callback, verify_khalti


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.all().order_by('-created_at')
    serializer_class = PaymentTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'head', 'options')

    def get_queryset(self):
        """Users only see their own payments; staff see everything."""
        qs = super().get_queryset()
        user = self.request.user
        return qs if user.is_staff else qs.filter(user=user)

    @transaction.atomic
    def perform_create(self, serializer):
        target_fields = serializer.validated_data
        payment = PaymentTransaction(user=self.request.user, gateway=target_fields['gateway'])
        for field in ('booking', 'guide_request', 'service_booking'):
            setattr(payment, field, target_fields.get(field))
        payment.amount, payment.currency = payable_amount(payment)
        existing = PaymentTransaction.objects.filter(
            user=self.request.user, status=PaymentTransaction.Status.PENDING,
            gateway=payment.gateway, booking=payment.booking,
            guide_request=payment.guide_request, service_booking=payment.service_booking,
        ).first()
        if existing:
            serializer.instance = existing
            if not existing.gateway_reference:
                initiate(existing)
            return
        payment.save()
        initiate(payment)
        serializer.instance = payment

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None, *args, **kwargs):
        """Complete an explicitly local demo payment; disabled in sandbox/live."""
        payment = self.get_object()
        if settings.PAYMENTS['MODE'] != 'demo' or payment.mode != 'demo':
            raise PermissionDenied('Manual confirmation is available only in local demo mode.')
        payment = mark_success(payment, metadata={'verified_by': 'local-demo'})
        return Response(PaymentTransactionSerializer(payment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None, *args, **kwargs):
        payment = self.get_object()
        if payment.status == PaymentTransaction.Status.SUCCESS:
            return Response(self.get_serializer(payment).data)
        if payment.mode == 'demo':
            raise ValidationError({'payment': 'Use confirm for a local demo payment.'})
        verified = payment.gateway == PaymentTransaction.Gateway.KHALTI and verify_khalti(payment)
        if not verified:
            return Response({'detail': 'The provider has not verified this payment.'}, status=status.HTTP_409_CONFLICT)
        payment.refresh_from_db()
        return Response(self.get_serializer(payment).data)


class EscrowLedgerViewSet(viewsets.ModelViewSet):
    queryset = EscrowLedger.objects.all().order_by('-created_at')
    serializer_class = EscrowLedgerSerializer
    permission_classes = (permissions.IsAdminUser,)
    http_method_names = ('get', 'head', 'options')


class KhaltiCallbackAPIView(APIView):
    serializer_class = PaymentCallbackResultSerializer
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        payment = PaymentTransaction.objects.filter(
            gateway=PaymentTransaction.Gateway.KHALTI,
            gateway_reference=request.query_params.get('pidx'),
        ).first()
        verified = bool(payment and verify_khalti(payment))
        return Response({'verified': verified}, status=status.HTTP_200_OK if verified else status.HTTP_400_BAD_REQUEST)


class EsewaCallbackAPIView(APIView):
    serializer_class = PaymentCallbackResultSerializer
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        encoded = request.query_params.get('data', '')
        # The signed payload contains the server-created transaction_uuid, so
        # locate the record only after decoding a non-authoritative copy.
        try:
            import base64, json
            reference = json.loads(base64.b64decode(encoded).decode()).get('transaction_uuid')
        except (ValueError, TypeError):
            reference = None
        payment = PaymentTransaction.objects.filter(
            gateway=PaymentTransaction.Gateway.ESEWA, gateway_reference=reference
        ).first()
        verified = bool(payment and verify_esewa_callback(payment, encoded))
        return Response({'verified': verified}, status=status.HTTP_200_OK if verified else status.HTTP_400_BAD_REQUEST)
