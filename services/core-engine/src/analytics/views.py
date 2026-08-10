from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import UserEvent
from .serializers import UserEventSerializer


class UserEventViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Ingest in-app events and (for admins) read the funnel.

    Authenticated clients log their own events; the actor is taken from the
    token, never the request body, so events cannot be spoofed onto other users.
    """

    serializer_class = UserEventSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ("event_type", "item_type", "item_id")
    ordering_fields = ("created_at",)

    def get_queryset(self):
        user = self.request.user
        qs = UserEvent.objects.all()
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(actor=user)

    def perform_create(self, serializer):
        serializer.save(actor=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def funnel(self, request, *args, **kwargs):
        """Event-type counts across all users — admin analytics."""
        return Response(UserEvent.objects.funnel())
