from __future__ import annotations

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.bookings.models import BookingSession

from .models import PaymentTransaction, EscrowLedger
from .serializers import PaymentTransactionSerializer, EscrowLedgerSerializer


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.all().order_by('-created_at')
    serializer_class = PaymentTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Users only see their own payments; staff see everything."""
        qs = super().get_queryset()
        user = self.request.user
        return qs if user.is_staff else qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None, *args, **kwargs):
        """Mark a payment as successful and confirm its booking.

        This stands in for real gateway verification (eSewa/Khalti sandbox
        callbacks), which is a later integration. It lets the app complete the
        booking -> payment -> confirmed flow end to end.
        """
        payment = self.get_object()
        payment.status = PaymentTransaction.Status.SUCCESS
        payment.gateway_reference = payment.gateway_reference or f'SIM-{timezone.now():%Y%m%d%H%M%S}'
        payment.save(update_fields=['status', 'gateway_reference', 'updated_at'])

        booking = payment.booking
        if booking and booking.status == BookingSession.Status.PENDING:
            booking.status = BookingSession.Status.CONFIRMED
            booking.save(update_fields=['status', 'updated_at'])

        return Response(
            PaymentTransactionSerializer(payment).data,
            status=status.HTTP_200_OK,
        )


class EscrowLedgerViewSet(viewsets.ModelViewSet):
    queryset = EscrowLedger.objects.all().order_by('-created_at')
    serializer_class = EscrowLedgerSerializer
    permission_classes = (permissions.IsAuthenticated,)
