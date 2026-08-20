from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingSessionViewSet, GuideRequestViewSet, ItineraryItemViewSet,
    TourPackageViewSet, TravelOfferingViewSet, TravelServiceBookingViewSet,
)

router = DefaultRouter()
router.register(r'packages', TourPackageViewSet, basename='package')
router.register(r'bookings', BookingSessionViewSet, basename='booking')
router.register(r'itinerary-items', ItineraryItemViewSet, basename='itineraryitem')
router.register(r'guide-requests', GuideRequestViewSet, basename='guide-request')
router.register(r'travel-offerings', TravelOfferingViewSet, basename='travel-offering')
router.register(r'travel-service-bookings', TravelServiceBookingViewSet, basename='travel-service-booking')

urlpatterns = [path('', include(router.urls))]
