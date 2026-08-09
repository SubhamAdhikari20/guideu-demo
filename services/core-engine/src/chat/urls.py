from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatMessageViewSet, ChatThreadViewSet

router = DefaultRouter()
router.register(r"threads", ChatThreadViewSet, basename="chatthread")
router.register(r"messages", ChatMessageViewSet, basename="chatmessage")

urlpatterns = [path("", include(router.urls))]
