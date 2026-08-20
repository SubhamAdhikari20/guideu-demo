from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from src.authentication.models import User
from src.bookings.models import TravelOffering, TravelServiceBooking

from src.payments.models import PaymentTransaction


@pytest.mark.django_db
def test_payment_uses_server_booking_total_and_demo_confirm_is_idempotent():
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
