from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from src.authentication.models import GuideProfile, User

from src.bookings.models import GuideRequest, ItineraryItem, TourPackage, BookingSession, TravelOffering


def user(username, role=User.Roles.TOURIST, **kwargs):
    return User.objects.create_user(username=username, email=f'{username}@example.com', password='Password123!', role=role, **kwargs)


@pytest.mark.django_db
def test_verified_available_guide_can_offer_and_tourist_can_accept():
    tourist = user('traveller')
    guide = user('guide', User.Roles.GUIDE, is_guide_verified=True)
    guide.guide_profile.availability = GuideProfile.Availability.AVAILABLE
    guide.guide_profile.save()
    tourist_client = APIClient(); tourist_client.force_authenticate(tourist)
    response = tourist_client.post('/api/v1/bookings/guide-requests/', {
        'pickup_name': 'Thamel', 'destination_name': 'Patan',
        'scheduled_at': (timezone.now() + timedelta(hours=2)).isoformat(),
        'duration_hours': 4, 'group_size': 2, 'proposed_fare': '2500.00',
    })
    assert response.status_code == 201
    request_id = response.data['id']

    guide_client = APIClient(); guide_client.force_authenticate(guide)
    offered = guide_client.post(f'/api/v1/bookings/guide-requests/{request_id}/offer/', {
        'offered_fare': '2400.00', 'eta_minutes': 12, 'message': 'Ready nearby.'
    })
    assert offered.status_code == 201
    accepted = tourist_client.post(f'/api/v1/bookings/guide-requests/{request_id}/accept-offer/', {'offer_id': offered.data['id']})
    assert accepted.status_code == 200
    assert accepted.data['accepted_guide'] == guide.id
    assert Decimal(accepted.data['final_fare']) == Decimal('2400.00')
    guide.refresh_from_db()
    assert guide.guide_profile.availability == GuideProfile.Availability.BUSY
    assert tourist.notifications.filter(title='New guide offer').exists()


@pytest.mark.django_db
def test_unverified_or_offline_guide_cannot_offer():
    tourist = user('traveller-two')
    guide = user('unverified-guide', User.Roles.GUIDE)
    guide_request = GuideRequest.objects.create(
        tourist=tourist, reference='GR-TEST-ONE', pickup_name='A', destination_name='B',
        recommended_fare=Decimal('2000.00')
    )
    client = APIClient(); client.force_authenticate(guide)
    response = client.post(f'/api/v1/bookings/guide-requests/{guide_request.id}/offer/', {'offered_fare': '2000.00'})
    assert response.status_code == 403


@pytest.mark.django_db
def test_travel_booking_total_is_server_owned_and_cancel_restores_inventory():
    tourist = user('hotel-guest')
    offering = TravelOffering.objects.create(
        service_type=TravelOffering.ServiceType.HOTEL, provider_name='Test Hotel',
        title='Two Night Room', location='Kathmandu', unit_price=Decimal('3000.00'),
        capacity=5, available_units=5,
    )
    client = APIClient(); client.force_authenticate(tourist)
    response = client.post('/api/v1/bookings/travel-service-bookings/', {
        'offering': offering.id, 'start_date': '2027-01-10', 'end_date': '2027-01-12',
        'travellers': 2, 'units': 1, 'total_price': '1.00',
    })
    assert response.status_code == 201
    assert Decimal(response.data['total_price']) == Decimal('6000.00')
    offering.refresh_from_db(); assert offering.available_units == 4
    cancelled = client.post(f"/api/v1/bookings/travel-service-bookings/{response.data['id']}/cancel/")
    assert cancelled.status_code == 200
    offering.refresh_from_db(); assert offering.available_units == 5


@pytest.mark.django_db
def test_itinerary_is_not_visible_or_editable_across_users():
    owner = user('trip-owner')
    stranger = user('trip-stranger')
    package = TourPackage.objects.create(title='Private trip', base_price=1000, duration_days=2)
    booking = BookingSession.objects.create(
        tourist=owner, tour_package=package, start_date=timezone.now().date() + timedelta(days=1),
        end_date=timezone.now().date() + timedelta(days=3), booking_reference='PRIVATE-ONE', total_price=1000,
    )
    item = ItineraryItem.objects.create(booking=booking, day_index=1, title='Private activity')
    client = APIClient(); client.force_authenticate(stranger)
    assert client.get(f'/api/v1/bookings/itinerary-items/{item.id}/').status_code == 404
    assert client.patch(f'/api/v1/bookings/itinerary-items/{item.id}/', {'title': 'Stolen'}).status_code == 404
