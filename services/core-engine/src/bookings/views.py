from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.db.models import Count, Sum
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from src.authentication.models import GuideProfile, User
from src.catalog.models import PricingBenchmark
from src.notifications.models import Notification
from src.notifications.services import create_notification

from .models import (
    BookingSession, GuideOffer, GuideRequest, ItineraryItem, TourPackage,
    TravelOffering, TravelServiceBooking,
)
from .serializers import (
    BookingSessionSerializer, GuideOfferSerializer, GuideRequestSerializer,
    ItineraryItemSerializer, TourPackageSerializer, TravelOfferingSerializer,
    TravelServiceBookingSerializer,
)


class TourPackageViewSet(viewsets.ModelViewSet):
    queryset = TourPackage.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = TourPackageSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title', 'description')
    ordering_fields = ('base_price', 'duration_days')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class BookingSessionViewSet(viewsets.ModelViewSet):
    queryset = BookingSession.objects.all().order_by('-created_at')
    serializer_class = BookingSessionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('booking_reference', 'tourist__username', 'assigned_guide__username')
    ordering_fields = ('start_date', 'end_date', 'status')

    def get_queryset(self):
        """Tourists see their own bookings (or the ones assigned to them as a
        guide); staff see everything."""
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        from django.db.models import Q
        return qs.filter(Q(tourist=user) | Q(assigned_guide=user))

    def perform_create(self, serializer):
        if self.request.user.role != User.Roles.TOURIST:
            raise PermissionDenied('Only tourists can create package bookings.')
        serializer.save(tourist=self.request.user)

    def update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Use the booking actions to change its lifecycle.')
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Bookings are retained for audit. Cancel the booking instead.')
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None, *args, **kwargs):
        booking = self.get_object()
        if not (request.user.is_staff or booking.tourist_id == request.user.id):
            raise PermissionDenied()
        if booking.status in (BookingSession.Status.COMPLETED, BookingSession.Status.CANCELLED):
            raise ValidationError({'status': 'This booking can no longer be cancelled.'})
        booking.status = BookingSession.Status.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        from src.payments.models import PaymentTransaction
        from src.payments.services import request_refund
        for payment in booking.payments.filter(status=PaymentTransaction.Status.SUCCESS):
            request_refund(payment, reason='Package booking cancelled.')
        return Response(self.get_serializer(booking).data)


class ItineraryItemViewSet(viewsets.ModelViewSet):
    queryset = ItineraryItem.objects.all()
    serializer_class = ItineraryItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = super().get_queryset().select_related('booking')
        if self.request.user.is_staff:
            return qs
        return qs.filter(Q(booking__tourist=self.request.user) | Q(booking__assigned_guide=self.request.user))

    def perform_create(self, serializer):
        booking = serializer.validated_data['booking']
        if not (self.request.user.is_staff or booking.tourist_id == self.request.user.id):
            raise PermissionDenied('You cannot edit another traveller’s itinerary.')
        serializer.save()

    def perform_update(self, serializer):
        if not (self.request.user.is_staff or serializer.instance.booking.tourist_id == self.request.user.id):
            raise PermissionDenied('Guides can view, but not rewrite, the traveller’s itinerary.')
        serializer.save()

    def perform_destroy(self, instance):
        if not (self.request.user.is_staff or instance.booking.tourist_id == self.request.user.id):
            raise PermissionDenied('Guides can view, but not delete, the traveller’s itinerary.')
        instance.delete()


class GuideRequestViewSet(viewsets.ModelViewSet):
    queryset = GuideRequest.objects.select_related('tourist', 'accepted_guide').prefetch_related('offers__guide')
    serializer_class = GuideRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'head', 'options')
    filterset_fields = ('status',)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        if user.role == User.Roles.GUIDE:
            return qs.filter(
                Q(status__in=[GuideRequest.Status.SEARCHING, GuideRequest.Status.OFFERED])
                | Q(accepted_guide=user) | Q(offers__guide=user)
            ).distinct()
        return qs.filter(tourist=user)

    def perform_create(self, serializer):
        if self.request.user.role != User.Roles.TOURIST:
            raise PermissionDenied('Only tourists can request a guide.')
        benchmark = PricingBenchmark.fair_price_for(service_type='Licensed Guide')
        base = Decimal(str(benchmark['fair_price_npr'])) if benchmark else Decimal('3000.00')
        hours = Decimal(str(serializer.validated_data.get('duration_hours', 4)))
        recommended = (base * max(hours / Decimal('8'), Decimal('0.5'))).quantize(Decimal('0.01'))
        guide_request = serializer.save(
            tourist=self.request.user,
            reference=f'GR-{uuid.uuid4().hex[:10].upper()}',
            recommended_fare=recommended,
        )
        create_notification(
            recipient_id=self.request.user.id, kind=Notification.Kind.BOOKING,
            title='Guide search started',
            body=f'Guides near {guide_request.pickup_name} can now send offers.',
            data={'guide_request_id': guide_request.id},
        )

    @action(detail=True, methods=['post'])
    def offer(self, request, pk=None, *args, **kwargs):
        guide_request = self.get_object()
        if request.user.role != User.Roles.GUIDE or not request.user.is_guide_verified:
            raise PermissionDenied('Only verified guides can send offers.')
        if request.user.guide_profile.availability != GuideProfile.Availability.AVAILABLE:
            raise ValidationError({'availability': 'Set your status to available before sending an offer.'})
        if guide_request.status not in (GuideRequest.Status.SEARCHING, GuideRequest.Status.OFFERED):
            raise ValidationError({'status': 'This request is no longer accepting offers.'})
        serializer = GuideOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer, created = GuideOffer.objects.update_or_create(
            guide_request=guide_request, guide=request.user,
            defaults={**serializer.validated_data, 'status': GuideOffer.Status.PENDING},
        )
        if guide_request.status == GuideRequest.Status.SEARCHING:
            guide_request.status = GuideRequest.Status.OFFERED
            guide_request.save(update_fields=['status', 'updated_at'])
        create_notification(
            recipient_id=guide_request.tourist_id, kind=Notification.Kind.BOOKING,
            title='New guide offer',
            body=f'{request.user.get_full_name() or request.user.username} offered NPR {offer.offered_fare}.',
            data={'guide_request_id': guide_request.id, 'offer_id': offer.id},
        )
        return Response(GuideOfferSerializer(offer).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='accept-offer')
    @transaction.atomic
    def accept_offer(self, request, pk=None, *args, **kwargs):
        guide_request = GuideRequest.objects.select_for_update().get(pk=self.get_object().pk)
        if guide_request.tourist_id != request.user.id:
            raise PermissionDenied('Only the traveller who created this request can accept an offer.')
        if guide_request.status not in (GuideRequest.Status.SEARCHING, GuideRequest.Status.OFFERED):
            raise ValidationError({'status': 'An offer has already been accepted.'})
        offer = guide_request.offers.select_related('guide').filter(pk=request.data.get('offer_id'), status=GuideOffer.Status.PENDING).first()
        if not offer:
            raise ValidationError({'offer_id': 'Choose a pending offer for this request.'})
        guide_request.offers.exclude(pk=offer.pk).filter(status=GuideOffer.Status.PENDING).update(status=GuideOffer.Status.DECLINED)
        offer.status = GuideOffer.Status.ACCEPTED
        offer.save(update_fields=['status', 'updated_at'])
        guide_request.accepted_guide = offer.guide
        guide_request.final_fare = offer.offered_fare
        guide_request.status = GuideRequest.Status.ACCEPTED
        guide_request.save(update_fields=['accepted_guide', 'final_fare', 'status', 'updated_at'])
        profile = offer.guide.guide_profile
        profile.availability = GuideProfile.Availability.BUSY
        profile.save(update_fields=['availability', 'updated_at'])
        create_notification(
            recipient_id=offer.guide_id, kind=Notification.Kind.BOOKING,
            title='Your guide offer was accepted', body=f'Request {guide_request.reference} is now assigned to you.',
            data={'guide_request_id': guide_request.id},
        )
        return Response(self.get_serializer(guide_request).data)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None, *args, **kwargs):
        guide_request = self.get_object()
        target = request.data.get('status')
        guide_steps = {
            GuideRequest.Status.ACCEPTED: GuideRequest.Status.EN_ROUTE,
            GuideRequest.Status.EN_ROUTE: GuideRequest.Status.ARRIVED,
            GuideRequest.Status.ARRIVED: GuideRequest.Status.ACTIVE,
            GuideRequest.Status.ACTIVE: GuideRequest.Status.COMPLETED,
        }
        if not (request.user.is_staff or guide_request.accepted_guide_id == request.user.id):
            raise PermissionDenied('Only the assigned guide can update trip progress.')
        if not request.user.is_staff and guide_steps.get(guide_request.status) != target:
            raise ValidationError({'status': 'Invalid next status for this trip.'})
        if target not in GuideRequest.Status.values:
            raise ValidationError({'status': 'Unknown trip status.'})
        guide_request.status = target
        guide_request.save(update_fields=['status', 'updated_at'])
        if target == GuideRequest.Status.COMPLETED and guide_request.accepted_guide:
            profile = guide_request.accepted_guide.guide_profile
            profile.availability = GuideProfile.Availability.AVAILABLE
            profile.save(update_fields=['availability', 'updated_at'])
            from src.payments.models import PaymentTransaction
            from src.payments.services import release_guide_escrow
            for payment in guide_request.payments.filter(status=PaymentTransaction.Status.SUCCESS):
                release_guide_escrow(payment)
        create_notification(
            recipient_id=guide_request.tourist_id, kind=Notification.Kind.BOOKING,
            title='Guide trip updated', body=f'{guide_request.reference} is now {guide_request.get_status_display().lower()}.',
            data={'guide_request_id': guide_request.id, 'status': target},
        )
        return Response(self.get_serializer(guide_request).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None, *args, **kwargs):
        guide_request = self.get_object()
        if not (request.user.is_staff or request.user.id in (guide_request.tourist_id, guide_request.accepted_guide_id)):
            raise PermissionDenied()
        if guide_request.status in (GuideRequest.Status.COMPLETED, GuideRequest.Status.CANCELLED):
            raise ValidationError({'status': 'This request can no longer be cancelled.'})
        guide_request.status = GuideRequest.Status.CANCELLED
        guide_request.cancelled_by = request.user
        guide_request.cancellation_reason = str(request.data.get('reason', ''))[:255]
        guide_request.save(update_fields=['status', 'cancelled_by', 'cancellation_reason', 'updated_at'])
        if guide_request.accepted_guide:
            profile = guide_request.accepted_guide.guide_profile
            profile.availability = GuideProfile.Availability.AVAILABLE
            profile.save(update_fields=['availability', 'updated_at'])
        from src.payments.models import PaymentTransaction
        from src.payments.services import request_refund
        for payment in guide_request.payments.filter(status=PaymentTransaction.Status.SUCCESS):
            request_refund(payment, reason='On-demand guide request cancelled.')
        other_id = guide_request.accepted_guide_id if request.user.id == guide_request.tourist_id else guide_request.tourist_id
        if other_id:
            create_notification(
                recipient_id=other_id, kind=Notification.Kind.BOOKING,
                title='Guide request cancelled', body=f'{guide_request.reference} was cancelled.',
                data={'guide_request_id': guide_request.id},
            )
        return Response(self.get_serializer(guide_request).data)

    @action(detail=False, methods=['get'])
    def earnings(self, request, *args, **kwargs):
        if request.user.role != User.Roles.GUIDE:
            raise PermissionDenied('Only guides have earnings.')
        from src.payments.models import EscrowLedger, PaymentTransaction
        successful = PaymentTransaction.objects.filter(
            guide_request__accepted_guide=request.user,
            status=PaymentTransaction.Status.SUCCESS,
        )
        released = EscrowLedger.objects.filter(
            transaction__in=successful, entry_type=EscrowLedger.EntryType.DEBIT,
            notes__icontains='released',
        ).aggregate(total=Sum('amount'), count=Count('id'))
        pending = successful.exclude(ledger_entries__entry_type=EscrowLedger.EntryType.DEBIT).aggregate(
            total=Sum('amount'), count=Count('id')
        )
        from django.db.models import Avg
        from src.reviews.models import Review
        ratings = Review.objects.filter(
            guide_account=request.user, status=Review.Status.APPROVED
        ).aggregate(average=Avg('rating'), count=Count('id'))
        return Response({
            'currency': 'NPR',
            'released_total': released['total'] or Decimal('0.00'),
            'released_trips': released['count'] or 0,
            'pending_total': pending['total'] or Decimal('0.00'),
            'pending_trips': pending['count'] or 0,
            'average_rating': round(ratings['average'] or 0, 2),
            'review_count': ratings['count'] or 0,
        })


class TravelOfferingViewSet(viewsets.ModelViewSet):
    queryset = TravelOffering.objects.all()
    serializer_class = TravelOfferingSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('service_type', 'location', 'origin', 'destination', 'is_active')
    search_fields = ('provider_name', 'title', 'location', 'origin', 'destination')
    ordering_fields = ('unit_price', 'departure_at')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if self.request.user.is_staff else qs.filter(is_active=True, available_units__gt=0)


class TravelServiceBookingViewSet(viewsets.ModelViewSet):
    queryset = TravelServiceBooking.objects.select_related('tourist', 'offering')
    serializer_class = TravelServiceBookingSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'head', 'options')
    filterset_fields = ('status', 'offering__service_type')

    def get_queryset(self):
        qs = super().get_queryset()
        return qs if self.request.user.is_staff else qs.filter(tourist=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        if self.request.user.role != User.Roles.TOURIST:
            raise PermissionDenied('Only tourists can book travel services.')
        offering = TravelOffering.objects.select_for_update().get(pk=serializer.validated_data['offering'].pk)
        units = serializer.validated_data.get('units', 1)
        travellers = serializer.validated_data.get('travellers', 1)
        if not offering.is_active or offering.available_units < units:
            raise ValidationError({'offering': 'This service has sold out.'})
        multiplier = units
        if offering.service_type == TravelOffering.ServiceType.HOTEL:
            multiplier *= (serializer.validated_data['end_date'] - serializer.validated_data['start_date']).days
        else:
            multiplier = travellers
        total = offering.unit_price * multiplier
        offering.available_units -= units if offering.service_type == TravelOffering.ServiceType.HOTEL else travellers
        offering.save(update_fields=['available_units', 'updated_at'])
        serializer.save(
            tourist=self.request.user, reference=f'TS-{uuid.uuid4().hex[:10].upper()}',
            total_price=total, currency=offering.currency,
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancel(self, request, pk=None, *args, **kwargs):
        service_booking = TravelServiceBooking.objects.select_for_update().select_related('offering').get(pk=self.get_object().pk)
        if service_booking.status in (TravelServiceBooking.Status.COMPLETED, TravelServiceBooking.Status.CANCELLED):
            raise ValidationError({'status': 'This booking can no longer be cancelled.'})
        service_booking.status = TravelServiceBooking.Status.CANCELLED
        service_booking.save(update_fields=['status', 'updated_at'])
        offering = service_booking.offering
        released = service_booking.units if offering.service_type == TravelOffering.ServiceType.HOTEL else service_booking.travellers
        offering.available_units = min(offering.capacity, offering.available_units + released)
        offering.save(update_fields=['available_units', 'updated_at'])
        from src.payments.models import PaymentTransaction
        from src.payments.services import request_refund
        for payment in service_booking.payments.filter(status=PaymentTransaction.Status.SUCCESS):
            request_refund(payment, reason='Travel service booking cancelled.')
        return Response(self.get_serializer(service_booking).data)
