"""Provider integration and server-side payment verification.

No browser redirect is trusted. Khalti is accepted only after its lookup API
returns ``Completed`` with the exact amount; eSewa callbacks must have a valid
HMAC signature and are then checked against the status API when configured.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from src.bookings.models import BookingSession, GuideRequest, TravelServiceBooking
from src.notifications.models import Notification
from src.notifications.services import create_notification

from .models import EscrowLedger, PaymentTransaction


def payable_amount(payment: PaymentTransaction) -> tuple[Decimal, str]:
    if payment.booking_id:
        return payment.booking.total_price, 'NPR'
    if payment.guide_request_id:
        if payment.guide_request.status not in (
            GuideRequest.Status.ACCEPTED, GuideRequest.Status.EN_ROUTE,
            GuideRequest.Status.ARRIVED, GuideRequest.Status.ACTIVE,
        ) or payment.guide_request.final_fare is None:
            raise ValidationError({'guide_request': 'Accept a guide offer before paying.'})
        return payment.guide_request.final_fare, payment.guide_request.currency
    if payment.service_booking_id:
        return payment.service_booking.total_price, payment.service_booking.currency
    raise ValidationError('A booking target is required.')


def _callback_url(provider: str) -> str:
    base = settings.PAYMENTS['PUBLIC_API_URL'].rstrip('/')
    return f'{base}/api/v1/payments/callbacks/{provider}/'


def initiate(payment: PaymentTransaction) -> dict[str, Any]:
    mode = settings.PAYMENTS['MODE']
    if mode not in {'demo', 'sandbox', 'live'}:
        raise ValidationError({'payment': 'PAYMENT_MODE must be demo, sandbox, or live.'})
    payment.mode = mode
    if mode == 'demo':
        payment.gateway_reference = f'DEMO-{uuid.uuid4().hex[:16].upper()}'
        payment.checkout_url = ''
        payment.gateway_metadata = {'message': 'Use the demo-confirm action to complete this local payment.'}
        payment.save(update_fields=['mode', 'gateway_reference', 'checkout_url', 'gateway_metadata', 'updated_at'])
        return payment.gateway_metadata
    if payment.gateway == PaymentTransaction.Gateway.KHALTI:
        return _initiate_khalti(payment)
    if payment.gateway == PaymentTransaction.Gateway.ESEWA:
        return _initiate_esewa(payment)
    raise ValidationError({'gateway': 'Sandbox/live payments support eSewa or Khalti only.'})


def _initiate_khalti(payment: PaymentTransaction) -> dict[str, Any]:
    config = settings.PAYMENTS['KHALTI']
    if not config['SECRET_KEY']:
        raise ValidationError({'gateway': 'Khalti is not configured on the server.'})
    payload = {
        'return_url': _callback_url('khalti'),
        'website_url': settings.PAYMENTS['PUBLIC_API_URL'],
        'amount': int(payment.amount * 100),
        'purchase_order_id': str(payment.id),
        'purchase_order_name': f'GuideU payment {payment.id}',
        'customer_info': {
            'name': payment.user.get_full_name() or payment.user.username,
            'email': payment.user.email,
            'phone': payment.user.phone_number or '9800000000',
        },
    }
    try:
        response = requests.post(
            f"{config['BASE_URL'].rstrip('/')}/api/v2/epayment/initiate/",
            json=payload, headers={'Authorization': f"Key {config['SECRET_KEY']}"}, timeout=12,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ValidationError({'gateway': 'Khalti initiation failed. Please try again.'}) from exc
    payment.gateway_reference = data['pidx']
    payment.checkout_url = data['payment_url']
    payment.expires_at = timezone.now() + timedelta(minutes=30)
    payment.gateway_metadata = {'expires_at': data.get('expires_at')}
    payment.save(update_fields=['gateway_reference', 'checkout_url', 'expires_at', 'gateway_metadata', 'updated_at'])
    return {'checkout_url': payment.checkout_url, 'pidx': payment.gateway_reference}


def _initiate_esewa(payment: PaymentTransaction) -> dict[str, Any]:
    config = settings.PAYMENTS['ESEWA']
    if not config['SECRET_KEY']:
        raise ValidationError({'gateway': 'eSewa is not configured on the server.'})
    transaction_uuid = f'{payment.id}-{uuid.uuid4().hex[:12]}'
    total_amount = str(payment.amount.quantize(Decimal('0.01')))
    signed_field_names = 'total_amount,transaction_uuid,product_code'
    message = f'total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={config["MERCHANT_CODE"]}'
    signature = base64.b64encode(
        hmac.new(config['SECRET_KEY'].encode(), message.encode(), hashlib.sha256).digest()
    ).decode()
    fields = {
        'amount': total_amount,
        'tax_amount': '0',
        'total_amount': total_amount,
        'transaction_uuid': transaction_uuid,
        'product_code': config['MERCHANT_CODE'],
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'success_url': _callback_url('esewa'),
        'failure_url': _callback_url('esewa'),
        'signed_field_names': signed_field_names,
        'signature': signature,
    }
    payment.gateway_reference = transaction_uuid
    payment.checkout_url = f"{config['BASE_URL'].rstrip('/')}/api/epay/main/v2/form"
    payment.gateway_metadata = {'form_fields': fields}
    payment.expires_at = timezone.now() + timedelta(minutes=30)
    payment.save(update_fields=['gateway_reference', 'checkout_url', 'gateway_metadata', 'expires_at', 'updated_at'])
    return {'checkout_url': payment.checkout_url, 'form_fields': fields}


def verify_khalti(payment: PaymentTransaction) -> bool:
    config = settings.PAYMENTS['KHALTI']
    try:
        response = requests.post(
            f"{config['BASE_URL'].rstrip('/')}/api/v2/epayment/lookup/",
            json={'pidx': payment.gateway_reference},
            headers={'Authorization': f"Key {config['SECRET_KEY']}"}, timeout=12,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return False
    if data.get('status') == 'Completed' and int(data.get('total_amount', -1)) == int(payment.amount * 100):
        mark_success(payment, metadata=data)
        return True
    return False


def verify_esewa_callback(payment: PaymentTransaction, encoded_data: str) -> bool:
    config = settings.PAYMENTS['ESEWA']
    try:
        import json
        data = json.loads(base64.b64decode(encoded_data).decode())
        signed_names = data['signed_field_names'].split(',')
        message = ','.join(f'{name}={data[name]}' for name in signed_names)
        expected = base64.b64encode(
            hmac.new(config['SECRET_KEY'].encode(), message.encode(), hashlib.sha256).digest()
        ).decode()
        valid_signature = hmac.compare_digest(expected, data['signature'])
        valid_amount = Decimal(str(data['total_amount']).replace(',', '')) == payment.amount
        valid_reference = data['transaction_uuid'] == payment.gateway_reference
        valid_status = data.get('status') == 'COMPLETE'
    except (KeyError, ValueError, TypeError, binascii.Error):
        return False
    provider_complete = False
    if valid_signature and valid_amount and valid_reference and valid_status:
        try:
            response = requests.get(
                f"{config['BASE_URL'].rstrip('/')}/api/epay/transaction/status/",
                params={
                    'product_code': config['MERCHANT_CODE'],
                    'total_amount': str(payment.amount.quantize(Decimal('0.01'))),
                    'transaction_uuid': payment.gateway_reference,
                },
                timeout=12,
            )
            response.raise_for_status()
            lookup = response.json()
            provider_complete = (
                lookup.get('status') == 'COMPLETE'
                and Decimal(str(lookup.get('total_amount', '-1')).replace(',', '')) == payment.amount
            )
        except (requests.RequestException, ValueError, TypeError):
            provider_complete = False
    if valid_signature and valid_amount and valid_reference and valid_status and provider_complete:
        mark_success(payment, metadata=data)
        return True
    return False


@transaction.atomic
def mark_success(payment: PaymentTransaction, *, metadata: dict[str, Any] | None = None) -> PaymentTransaction:
    payment = PaymentTransaction.objects.select_for_update().get(pk=payment.pk)
    if payment.status == PaymentTransaction.Status.SUCCESS:
        return payment
    payment.status = PaymentTransaction.Status.SUCCESS
    payment.verified_at = timezone.now()
    payment.gateway_metadata = metadata or payment.gateway_metadata
    payment.failure_reason = ''
    payment.save(update_fields=['status', 'verified_at', 'gateway_metadata', 'failure_reason', 'updated_at'])
    EscrowLedger.objects.create(
        transaction=payment, entry_type=EscrowLedger.EntryType.CREDIT,
        amount=payment.amount, balance=payment.amount, notes='Verified customer payment held in escrow.'
    )
    if payment.booking_id and payment.booking.status == BookingSession.Status.PENDING:
        payment.booking.status = BookingSession.Status.CONFIRMED
        payment.booking.save(update_fields=['status', 'updated_at'])
    if payment.service_booking_id and payment.service_booking.status == TravelServiceBooking.Status.PAYMENT_PENDING:
        payment.service_booking.status = TravelServiceBooking.Status.CONFIRMED
        payment.service_booking.save(update_fields=['status', 'updated_at'])
    create_notification(
        recipient_id=payment.user_id, kind=Notification.Kind.PAYMENT,
        title='Payment verified', body=f'Your payment of {payment.currency} {payment.amount} was successful.',
        data={'payment_id': payment.id},
    )
    return payment


@transaction.atomic
def request_refund(payment: PaymentTransaction, *, reason: str) -> PaymentTransaction:
    """Refund a local demo immediately; queue provider refunds for moderation."""
    payment = PaymentTransaction.objects.select_for_update().get(pk=payment.pk)
    if payment.status in (PaymentTransaction.Status.REFUNDED, PaymentTransaction.Status.REFUND_PENDING):
        return payment
    if payment.status != PaymentTransaction.Status.SUCCESS:
        return payment
    if payment.mode == 'demo':
        payment.status = PaymentTransaction.Status.REFUNDED
        EscrowLedger.objects.get_or_create(
            transaction=payment, entry_type=EscrowLedger.EntryType.DEBIT,
            defaults={'amount': payment.amount, 'balance': Decimal('0.00'), 'notes': reason},
        )
    else:
        payment.status = PaymentTransaction.Status.REFUND_PENDING
    payment.failure_reason = reason
    payment.save(update_fields=['status', 'failure_reason', 'updated_at'])
    create_notification(
        recipient_id=payment.user_id, kind=Notification.Kind.PAYMENT,
        title='Refund update',
        body='Your refund was completed.' if payment.status == PaymentTransaction.Status.REFUNDED else 'Your provider refund is awaiting administrator processing.',
        data={'payment_id': payment.id, 'status': payment.status},
    )
    return payment


@transaction.atomic
def release_guide_escrow(payment: PaymentTransaction) -> None:
    """Append a payout ledger entry once a paid guide trip is completed."""
    payment = PaymentTransaction.objects.select_for_update().get(pk=payment.pk)
    if payment.status != PaymentTransaction.Status.SUCCESS:
        return
    EscrowLedger.objects.get_or_create(
        transaction=payment, entry_type=EscrowLedger.EntryType.DEBIT,
        defaults={
            'amount': payment.amount, 'balance': Decimal('0.00'),
            'notes': 'Guide trip completed; escrow released for payout.',
        },
    )
