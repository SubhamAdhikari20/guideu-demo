from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from src.authentication.models import User
from src.bookings.models import BookingSession, TourPackage


@pytest.fixture
def people(db):
    tourist = User.objects.create_user(email="tourist@e.com", username="tourist", password="pass12345")
    guide = User.objects.create_user(
        email="guide@e.com", username="guide", password="pass12345", role=User.Roles.GUIDE
    )
    outsider = User.objects.create_user(email="out@e.com", username="out", password="pass12345")
    return tourist, guide, outsider


@pytest.fixture
def booking(people):
    tourist, guide, _ = people
    package = TourPackage.objects.create(title="EBC Trek", base_price=120000, duration_days=14)
    return BookingSession.objects.create(
        tourist=tourist, tour_package=package, assigned_guide=guide,
        booking_reference="BK-1", start_date="2026-10-01", end_date="2026-10-14",
    )


def auth(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_message_is_stored_and_visible_to_both_parties(people, booking):
    tourist, guide, _ = people
    room = f"booking:{booking.pk}"

    sent = auth(tourist).post("/api/v1/chat/messages/", {"room": room, "body": "Namaste!"})
    assert sent.status_code == 201

    # The guide, the other party on the booking, can read the history.
    history = auth(guide).get(f"/api/v1/chat/messages/?room={room}")
    assert history.status_code == 200
    assert [m["body"] for m in history.json()] == ["Namaste!"]


@pytest.mark.django_db
def test_outsider_cannot_read_or_post_to_a_booking_room(people, booking):
    _, _, outsider = people
    room = f"booking:{booking.pk}"
    assert auth(outsider).get(f"/api/v1/chat/messages/?room={room}").status_code == 403
    assert auth(outsider).post("/api/v1/chat/messages/", {"room": room, "body": "hi"}).status_code == 403


@pytest.mark.django_db
def test_reading_clears_unread_count_for_the_reader(people, booking):
    tourist, guide, _ = people
    room = f"booking:{booking.pk}"
    auth(tourist).post("/api/v1/chat/messages/", {"room": room, "body": "u there?"})

    threads = auth(guide).get("/api/v1/chat/threads/").json()
    rows = threads["results"] if isinstance(threads, dict) else threads
    assert rows[0]["unread_count"] == 1

    auth(guide).get(f"/api/v1/chat/messages/?room={room}")  # reading marks read
    threads = auth(guide).get("/api/v1/chat/threads/").json()
    rows = threads["results"] if isinstance(threads, dict) else threads
    assert rows[0]["unread_count"] == 0
