from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from src.authentication.models import TimeStampedModel, User


class TourPackage(TimeStampedModel):
    """A tour package offering that tourists can book.

    This model is intended to be read-heavy and cached by the realtime
    services when needed.
    """

    title = models.CharField(max_length=255, help_text='Display title for the tour package')
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Base price in platform currency')
    duration_days = models.PositiveSmallIntegerField(default=1, help_text='Typical duration in days')
    capacity = models.PositiveSmallIntegerField(default=1, help_text='Max number of tourists allowed')
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = 'tour package'
        verbose_name_plural = 'tour packages'

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title


class BookingSession(TimeStampedModel):
    """Represents a booking lifecycle for a tourist on a given `TourPackage`.

    Status lifecycle: PENDING -> CONFIRMED -> ACTIVE -> COMPLETED | CANCELLED
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tourist = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='bookings', db_index=True)
    tour_package = models.ForeignKey('bookings.TourPackage', on_delete=models.PROTECT, related_name='bookings', db_index=True)
    # Optional link to a dataset-backed trekking route (additive, non-breaking).
    route = models.ForeignKey('catalog.TrekkingRoute', on_delete=models.PROTECT, null=True, blank=True, related_name='bookings', db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    assigned_guide = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bookings', db_index=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    booking_reference = models.CharField(max_length=64, unique=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'booking session'
        verbose_name_plural = 'booking sessions'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['tourist']),
            models.Index(fields=['assigned_guide']),
        ]

    def clean(self) -> None:
        if self.end_date <= self.start_date:
            raise ValidationError({'end_date': 'end_date must be after start_date'})
        if self.assigned_guide and self.assigned_guide.role != User.Roles.GUIDE:
            raise ValidationError({'assigned_guide': 'Assigned user must be a guide'})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class ItineraryItem(TimeStampedModel):
    booking = models.ForeignKey('bookings.BookingSession', on_delete=models.CASCADE, related_name='itinerary_items', db_index=True)
    day_index = models.PositiveIntegerField(help_text='Day number within the tour, starting from 1')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.JSONField(blank=True, null=True, help_text='Geo location or place metadata (GeoJSON)')
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'itinerary item'
        verbose_name_plural = 'itinerary items'
        ordering = ['booking', 'day_index']

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.booking.booking_reference} - Day {self.day_index}: {self.title}"


class GuideRequest(TimeStampedModel):
    """An on-demand guide request with a bid/offer lifecycle."""

    class Status(models.TextChoices):
        SEARCHING = 'SEARCHING', 'Searching for guides'
        OFFERED = 'OFFERED', 'Offers received'
        ACCEPTED = 'ACCEPTED', 'Guide accepted'
        EN_ROUTE = 'EN_ROUTE', 'Guide en route'
        ARRIVED = 'ARRIVED', 'Guide arrived'
        ACTIVE = 'ACTIVE', 'Trip active'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    tourist = models.ForeignKey(
        'authentication.User', on_delete=models.CASCADE, related_name='guide_requests'
    )
    accepted_guide = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='accepted_guide_requests'
    )
    reference = models.CharField(max_length=16, unique=True, db_index=True)
    pickup_name = models.CharField(max_length=180)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_name = models.CharField(max_length=180)
    destination_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    duration_hours = models.PositiveSmallIntegerField(default=4)
    group_size = models.PositiveSmallIntegerField(default=1)
    requirements = models.TextField(blank=True)
    proposed_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recommended_fare = models.DecimalField(max_digits=10, decimal_places=2)
    final_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default='NPR')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SEARCHING, db_index=True)
    cancelled_by = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cancelled_guide_requests'
    )
    cancellation_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'scheduled_at'])]

    def clean(self) -> None:
        if self.group_size < 1:
            raise ValidationError({'group_size': 'At least one traveller is required.'})
        if self.accepted_guide_id and self.accepted_guide.role != User.Roles.GUIDE:
            raise ValidationError({'accepted_guide': 'Accepted user must be a guide.'})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class GuideOffer(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    guide_request = models.ForeignKey(GuideRequest, on_delete=models.CASCADE, related_name='offers')
    guide = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='guide_offers')
    offered_fare = models.DecimalField(max_digits=10, decimal_places=2)
    eta_minutes = models.PositiveSmallIntegerField(default=15)
    message = models.CharField(max_length=280, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        ordering = ['offered_fare', 'eta_minutes']
        constraints = [
            models.UniqueConstraint(fields=['guide_request', 'guide'], name='unique_offer_per_guide_request')
        ]


class TravelOffering(TimeStampedModel):
    """Locally managed hotel, flight, and bus inventory for the thesis demo."""

    class ServiceType(models.TextChoices):
        HOTEL = 'HOTEL', 'Hotel'
        FLIGHT = 'FLIGHT', 'Flight'
        BUS = 'BUS', 'Bus'

    service_type = models.CharField(max_length=8, choices=ServiceType.choices, db_index=True)
    provider_name = models.CharField(max_length=140)
    title = models.CharField(max_length=180)
    location = models.CharField(max_length=140, blank=True, db_index=True)
    origin = models.CharField(max_length=140, blank=True, db_index=True)
    destination = models.CharField(max_length=140, blank=True, db_index=True)
    departure_at = models.DateTimeField(null=True, blank=True, db_index=True)
    arrival_at = models.DateTimeField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default='NPR')
    capacity = models.PositiveIntegerField(default=1)
    available_units = models.PositiveIntegerField(default=1)
    image_url = models.URLField(blank=True)
    amenities = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['unit_price', 'departure_at']
        indexes = [models.Index(fields=['service_type', 'origin', 'destination'])]

    def clean(self) -> None:
        if self.available_units > self.capacity:
            raise ValidationError({'available_units': 'Available units cannot exceed capacity.'})
        if self.service_type == self.ServiceType.HOTEL and not self.location:
            raise ValidationError({'location': 'A hotel location is required.'})
        if self.service_type != self.ServiceType.HOTEL and (not self.origin or not self.destination):
            raise ValidationError({'origin': 'Origin and destination are required.'})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class TravelServiceBooking(TimeStampedModel):
    class Status(models.TextChoices):
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tourist = models.ForeignKey(
        'authentication.User', on_delete=models.CASCADE, related_name='travel_service_bookings'
    )
    offering = models.ForeignKey(TravelOffering, on_delete=models.PROTECT, related_name='bookings')
    reference = models.CharField(max_length=16, unique=True, db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    travellers = models.PositiveSmallIntegerField(default=1)
    units = models.PositiveSmallIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='NPR')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PAYMENT_PENDING, db_index=True
    )
    passenger_details = models.JSONField(default=list, blank=True)
    special_requests = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self) -> None:
        if self.travellers < 1 or self.units < 1:
            raise ValidationError('Travellers and units must both be positive.')
        if self.offering_id and self.offering.service_type == TravelOffering.ServiceType.HOTEL:
            if not self.start_date or not self.end_date or self.end_date <= self.start_date:
                raise ValidationError({'end_date': 'Hotel checkout must be after check-in.'})
