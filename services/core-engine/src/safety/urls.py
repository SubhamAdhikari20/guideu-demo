from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SosAlertViewSet

router = DefaultRouter()
router.register(r"sos", SosAlertViewSet, basename="sos-alert")

urlpatterns = [path("", include(router.urls))]
