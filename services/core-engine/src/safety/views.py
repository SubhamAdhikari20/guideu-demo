from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SosAlert
from .serializers import SosAlertSerializer


class SosAlertViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Raise and track SOS alerts.

    Tourists raise and see their own alerts; staff see everyone's so they can
    respond. Either the owner or staff can mark an alert resolved.
    """

    serializer_class = SosAlertSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ("status",)

    def get_queryset(self):
        user = self.request.user
        qs = SosAlert.objects.select_related("user")
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, *args, **kwargs):
        alert = self.get_object()
        alert.resolve()
        return Response(SosAlertSerializer(alert).data)
