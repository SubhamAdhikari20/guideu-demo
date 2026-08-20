from django.contrib import admin

from .models import (
    BookingSession, GuideOffer, GuideRequest, ItineraryItem, TourPackage,
    TravelOffering, TravelServiceBooking,
)


@admin.register(TourPackage)
class TourPackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'base_price', 'duration_days', 'capacity', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration_days')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BookingSession)
class BookingSessionAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'tourist', 'tour_package', 'status', 'assigned_guide', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'tour_package')
    search_fields = ('booking_reference', 'tourist__username', 'assigned_guide__username')
    readonly_fields = ('created_at', 'updated_at')


class ItineraryInline(admin.TabularInline):
    model = ItineraryItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


BookingSessionAdmin.inlines = (ItineraryInline,)


class GuideOfferInline(admin.TabularInline):
    model = GuideOffer
    extra = 0


@admin.register(GuideRequest)
class GuideRequestAdmin(admin.ModelAdmin):
    list_display = ('reference', 'tourist', 'accepted_guide', 'status', 'scheduled_at', 'final_fare')
    list_filter = ('status',)
    search_fields = ('reference', 'tourist__email', 'accepted_guide__email', 'pickup_name', 'destination_name')
    inlines = (GuideOfferInline,)


@admin.register(TravelOffering)
class TravelOfferingAdmin(admin.ModelAdmin):
    list_display = ('title', 'service_type', 'provider_name', 'unit_price', 'available_units', 'is_active')
    list_filter = ('service_type', 'is_active')
    search_fields = ('title', 'provider_name', 'location', 'origin', 'destination')


@admin.register(TravelServiceBooking)
class TravelServiceBookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'tourist', 'offering', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'offering__service_type')
    search_fields = ('reference', 'tourist__email', 'offering__title')
