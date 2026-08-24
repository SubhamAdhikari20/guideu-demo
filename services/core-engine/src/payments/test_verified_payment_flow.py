from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from src.authentication.models import User
from src.bookings.models import TravelOffering, TravelServiceBooking

from src.payments.models import PaymentTransaction
from src.payments.serializers import PaymentTransactionSerializer


@pytest.fixture
def demo_mode(settings):
    """Pin PAYMENT_MODE to demo for tests that use the local confirm path.

    Without this the suite inherits whatever the developer's .env says. Setting
    the project to sandbox mode turned every demo-confirm call into a 403 and
    failed two tests that were not actually broken."""
    payments = dict(settings.PAYMENTS)
    payments['MODE'] = 'demo'
    settings.PAYMENTS = payments
    return payments


def test_server_owned_payment_fields_are_read_only():
    serializer = PaymentTransactionSerializer()
    for field in (
        'amount', 'currency', 'status', 'gateway_reference', 'mode',
        'checkout_url', 'expires_at', 'verified_at', 'failure_reason', 'created_at',
    ):
        assert serializer.fields[field].read_only, field


@pytest.mark.django_db
def test_payment_uses_server_booking_total_and_demo_confirm_is_idempotent(demo_mode):
    tourist = User.objects.create_user(username='payer', email='payer@example.com', password='Password123!')
    offering = TravelOffering.objects.create(
        service_type=TravelOffering.ServiceType.BUS, provider_name='Bus', title='KTM Pokhara',
        origin='Kathmandu', destination='Pokhara', departure_at=timezone.now() + timedelta(days=2),
        unit_price=Decimal('1800.00'), capacity=40, available_units=39,
    )
    booking = TravelServiceBooking.objects.create(
        tourist=tourist, offering=offering, reference='TS-PAY-ONE', travellers=1, units=1,
        total_price=Decimal('1800.00')
    )
    client = APIClient(); client.force_authenticate(tourist)
    created = client.post('/api/v1/payments/payments/', {
        'service_booking': booking.id, 'gateway': 'ESEWA', 'amount': '1.00'
    })
    assert created.status_code == 201
    assert Decimal(created.data['amount']) == Decimal('1800.00')
    first = client.post(f"/api/v1/payments/payments/{created.data['id']}/confirm/")
    second = client.post(f"/api/v1/payments/payments/{created.data['id']}/confirm/")
    assert first.status_code == second.status_code == 200
    assert first.data['status'] == PaymentTransaction.Status.SUCCESS
    assert PaymentTransaction.objects.get(pk=created.data['id']).ledger_entries.count() == 1
    receipt = client.get(f"/api/v1/payments/payments/{created.data['id']}/receipt/")
    assert receipt.status_code == 200
    assert receipt.data['receipt_number'] == f"GUIDEU-{created.data['id']:08d}"
    assert receipt.data['amount'] == '1800.00'
    assert receipt.data['item'] == {
        'type': 'Bus', 'reference': 'TS-PAY-ONE', 'title': 'KTM Pokhara',
    }
    booking.refresh_from_db(); assert booking.status == TravelServiceBooking.Status.CONFIRMED
    cancelled = client.post(f'/api/v1/bookings/travel-service-bookings/{booking.id}/cancel/')
    assert cancelled.status_code == 200
    payment = PaymentTransaction.objects.get(pk=created.data['id'])
    assert payment.status == PaymentTransaction.Status.REFUNDED
    assert payment.ledger_entries.count() == 2


@pytest.mark.django_db
def test_user_cannot_pay_for_another_users_booking():
    owner = User.objects.create_user(username='owner-pay', email='owner-pay@example.com', password='Password123!')
    stranger = User.objects.create_user(username='stranger-pay', email='stranger-pay@example.com', password='Password123!')
    offering = TravelOffering.objects.create(
        service_type=TravelOffering.ServiceType.HOTEL, provider_name='Hotel', title='Room', location='Kathmandu',
        unit_price=Decimal('2000.00'), capacity=3, available_units=2,
    )
    booking = TravelServiceBooking.objects.create(
        tourist=owner, offering=offering, reference='TS-OWNER', travellers=1, units=1,
        start_date=timezone.now().date() + timedelta(days=1), end_date=timezone.now().date() + timedelta(days=2),
        total_price=Decimal('2000.00')
    )
    client = APIClient(); client.force_authenticate(stranger)
    response = client.post('/api/v1/payments/payments/', {'service_booking': booking.id, 'gateway': 'KHALTI'})
    assert response.status_code == 400
    assert PaymentTransaction.objects.count() == 0


@pytest.mark.django_db
def test_pending_payment_has_no_receipt_and_receipt_is_owner_scoped(demo_mode):
    owner = User.objects.create_user(username='receipt-owner', email='receipt-owner@example.com', password='Password123!')
    stranger = User.objects.create_user(username='receipt-stranger', email='receipt-stranger@example.com', password='Password123!')
    offering = TravelOffering.objects.create(
        service_type=TravelOffering.ServiceType.FLIGHT, provider_name='Air', title='KTM BWA',
        origin='Kathmandu', destination='Bhairahawa', departure_at=timezone.now() + timedelta(days=2),
        unit_price=Decimal('6500.00'), capacity=40, available_units=39,
    )
    booking = TravelServiceBooking.objects.create(
        tourist=owner, offering=offering, reference='TS-RECEIPT', travellers=1, units=1,
        total_price=Decimal('6500.00')
    )
    owner_client = APIClient(); owner_client.force_authenticate(owner)
    created = owner_client.post('/api/v1/payments/payments/', {
        'service_booking': booking.id, 'gateway': 'KHALTI'
    })
    pending = owner_client.get(f"/api/v1/payments/payments/{created.data['id']}/receipt/")
    assert pending.status_code == 400

    owner_client.post(f"/api/v1/payments/payments/{created.data['id']}/confirm/")
    stranger_client = APIClient(); stranger_client.force_authenticate(stranger)
    hidden = stranger_client.get(f"/api/v1/payments/payments/{created.data['id']}/receipt/")
    assert hidden.status_code == 404
