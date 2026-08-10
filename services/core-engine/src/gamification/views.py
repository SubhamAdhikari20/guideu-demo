from __future__ import annotations

from django.db.models import Count, Sum
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from src.common.permissions import IsAdminOrReadOnly

from .models import Badge, BadgeAward
from .serializers import BadgeAwardSerializer, BadgeSerializer, LeaderboardEntrySerializer


class BadgeViewSet(viewsets.ModelViewSet):
    """Badge catalog — public read, admin write."""

    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_fields = ("category",)
    search_fields = ("name", "trigger_event")


class BadgeAwardViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """A user's earned badges, plus a global leaderboard."""

    serializer_class = BadgeAwardSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ("badge",)

    def get_queryset(self):
        user = self.request.user
        qs = BadgeAward.objects.select_related("badge", "user")
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["get"])
    def me(self, request, *args, **kwargs):
        awards = BadgeAward.objects.filter(user=request.user).select_related("badge")
        total = awards.aggregate(points=Sum("points_awarded"))["points"] or 0
        return Response({"total_points": total, "badges": BadgeAwardSerializer(awards, many=True).data})

    @action(detail=False, methods=["get"])
    def leaderboard(self, request, *args, **kwargs):
        rows = (
            BadgeAward.objects.values("user_id", "user__username")
            .annotate(total_points=Sum("points_awarded"), badge_count=Count("id"))
            .order_by("-total_points")[:20]
        )
        data = [
            {
                "user_id": r["user_id"],
                "username": r["user__username"],
                "total_points": r["total_points"] or 0,
                "badge_count": r["badge_count"],
            }
            for r in rows
        ]
        return Response(LeaderboardEntrySerializer(data, many=True).data)
