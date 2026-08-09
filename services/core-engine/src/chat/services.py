"""Thread resolution helpers shared by the views.

Keeping the ``room -> thread + participants`` logic here means both the REST
create and list paths stay consistent, and a ``booking:<id>`` room always has the
right two people on it (the tourist and the assigned guide).
"""
from __future__ import annotations

from .models import ChatThread


def get_or_create_thread(room: str) -> ChatThread:
    """Fetch (or open) the thread for a room and keep its participants in sync."""
    thread, _ = ChatThread.objects.get_or_create(room=room)
    if room.startswith("booking:"):
        _sync_booking_participants(thread, room)
    return thread


def _sync_booking_participants(thread: ChatThread, room: str) -> None:
    try:
        booking_id = int(room.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    from src.bookings.models import BookingSession

    booking = (
        BookingSession.objects.filter(pk=booking_id)
        .select_related("tourist", "assigned_guide")
        .first()
    )
    if booking is None:
        return
    people = [booking.tourist]
    if booking.assigned_guide:
        people.append(booking.assigned_guide)
    thread.participants.add(*[u for u in people if u is not None])
