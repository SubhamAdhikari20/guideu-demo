from __future__ import annotations

from typing import Any

from rest_framework import serializers

from src.authentication.models import User
from .models import (
    BookingSession, GuideOffer, GuideRequest, ItineraryItem, TourPackage,
    TravelOffering, TravelServiceBooking,
)


class TourPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourPackage
        fields = ('id', 'title', 'description', 'base_price', 'duration_days', 'capacity', 'is_active', 'created_at')


class ItineraryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryItem
        fields = ('id', 'booking', 'day_index', 'title', 'description', 'location', 'start_time', 'end_time')


class BookingSessionSerializer(serializers.ModelSerializer):
    itinerary_items = ItineraryItemSerializer(many=True, read_only=True)
    # The tourist is taken from the logged-in user in the view, so clients never
    # send (or spoof) it.
    tourist = serializers.PrimaryKeyRelatedField(read_only=True)
    tour_package_title = serializers.CharField(source='tour_package.title', read_only=True)
    assigned_guide = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = BookingSession
        fields = ('id', 'booking_reference', 'tourist', 'tour_package', 'tour_package_title', 'route', 'start_date', 'end_date', 'status', 'assigned_guide', 'total_price', 'notes', 'itinerary_items')
        read_only_fields = ('booking_reference', 'total_price')

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        end = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_date': 'end_date must be after start_date'})
        guide = data.get('assigned_guide')
        if guide and not guide.is_guide_verified:
            raise serializers.ValidationError({'assigned_guide': 'Guide must be verified to be assigned to bookings.'})
        return data

    def create(self, validated_data: dict[str, Any]) -> BookingSession:
        # Compute total_price simply as base_price for now; complex pricing belongs to a service layer
        tour = validated_data['tour_package']
        validated_data['total_price'] = tour.base_price
        # Create a unique booking reference
        import uuid

        validated_data['booking_reference'] = uuid.uuid4().hex[:12].upper()
        return super().create(validated_data)


class GuideOfferSerializer(serializers.ModelSerializer):
    guide_name = serializers.SerializerMethodField()
    guide_rating = serializers.SerializerMethodField()

    class Meta:
        model = GuideOffer
        fields = (
            'id', 'guide', 'guide_name', 'guide_rating', 'offered_fare', 'eta_minutes',
            'message', 'status', 'created_at'
        )
        read_only_fields = ('guide', 'status', 'created_at')

    def get_guide_name(self, obj: GuideOffer) -> str:
        return obj.guide.get_full_name() or obj.guide.username

    def get_guide_rating(self, obj: GuideOffer) -> float:
        registry = getattr(getattr(obj.guide, 'guide_profile', None), 'registry_entry', None)
        return float(registry.average_rating) if registry else 0.0

    def validate_offered_fare(self, value):
        if value <= 0:
            raise serializers.ValidationError('Offer must be positive.')
        return value


class GuideRequestSerializer(serializers.ModelSerializer):
    tourist_name = serializers.SerializerMethodField()
    accepted_guide_name = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()

    class Meta:
        model = GuideRequest
        fields = (
            'id', 'reference', 'tourist', 'tourist_name', 'accepted_guide',
            'accepted_guide_name', 'pickup_name', 'pickup_latitude', 'pickup_longitude',
            'destination_name', 'destination_latitude', 'destination_longitude',
            'scheduled_at', 'duration_hours', 'group_size', 'requirements',
            'proposed_fare', 'recommended_fare', 'final_fare', 'currency', 'status',
            'cancellation_reason', 'offers', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'reference', 'tourist', 'accepted_guide', 'recommended_fare', 'final_fare',
            'currency', 'status', 'cancellation_reason', 'created_at', 'updated_at'
        )

    def get_tourist_name(self, obj: GuideRequest) -> str:
        return obj.tourist.get_full_name() or obj.tourist.username

    def get_accepted_guide_name(self, obj: GuideRequest) -> str | None:
        if not obj.accepted_guide:
            return None
        return obj.accepted_guide.get_full_name() or obj.accepted_guide.username

    def get_offers(self, obj: GuideRequest) -> list[dict[str, Any]]:
        request = self.context.get('request')
        offers = obj.offers.select_related('guide').all()
        if request and request.user.role == User.Roles.GUIDE and not request.user.is_staff:
            offers = offers.filter(guide=request.user)
        return GuideOfferSerializer(offers, many=True).data


class TravelOfferingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelOffering
        fields = (
            'id', 'service_type', 'provider_name', 'title', 'location', 'origin',
            'destination', 'departure_at', 'arrival_at', 'unit_price', 'currency',
            'capacity', 'available_units', 'image_url', 'amenities', 'metadata', 'is_active'
        )

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        service_type = data.get('service_type', getattr(self.instance, 'service_type', None))
        if service_type == TravelOffering.ServiceType.HOTEL and not data.get('location', getattr(self.instance, 'location', '')):
            raise serializers.ValidationError({'location': 'A hotel location is required.'})
        if service_type != TravelOffering.ServiceType.HOTEL:
            if not data.get('origin', getattr(self.instance, 'origin', '')) or not data.get('destination', getattr(self.instance, 'destination', '')):
                raise serializers.ValidationError({'origin': 'Origin and destination are required.'})
        available = data.get('available_units', getattr(self.instance, 'available_units', 0))
        capacity = data.get('capacity', getattr(self.instance, 'capacity', 0))
        if available > capacity:
            raise serializers.ValidationError({'available_units': 'Available units cannot exceed capacity.'})
        return data


class TravelServiceBookingSerializer(serializers.ModelSerializer):
    offering_details = TravelOfferingSerializer(source='offering', read_only=True)

    class Meta:
        model = TravelServiceBooking
        fields = (
            'id', 'reference', 'tourist', 'offering', 'offering_details', 'start_date',
            'end_date', 'travellers', 'units', 'total_price', 'currency', 'status',
            'passenger_details', 'special_requests', 'created_at'
        )
        read_only_fields = ('reference', 'tourist', 'total_price', 'currency', 'status', 'created_at')

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        offering = data.get('offering')
        units = data.get('units', 1)
        travellers = data.get('travellers', 1)
        required_inventory = (
            units if offering and offering.service_type == TravelOffering.ServiceType.HOTEL else travellers
        )
        if offering and (not offering.is_active or offering.available_units < required_inventory):
            raise serializers.ValidationError({'offering': 'This service does not have enough availability.'})
        if offering and offering.service_type == TravelOffering.ServiceType.HOTEL:
            start, end = data.get('start_date'), data.get('end_date')
            if not start or not end or end <= start:
                raise serializers.ValidationError({'end_date': 'Checkout must be after check-in.'})
        return data
