from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TravelWorkspaceViewSet, WorkspaceItemViewSet

router = DefaultRouter()
router.register(r"trips", TravelWorkspaceViewSet, basename="workspace-trip")
router.register(r"items", WorkspaceItemViewSet, basename="workspace-item")

urlpatterns = [path("", include(router.urls))]
