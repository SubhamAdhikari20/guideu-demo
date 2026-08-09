from __future__ import annotations

import calendar
from datetime import date

from django.core.cache import cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from src.common.permissions import IsAdminOrReadOnly

from .filters import (
    CulturalEventFilter,
    GuideRegistryFilter,
    PricingBenchmarkFilter,
    TrekkingRouteFilter,
)
from .models import (
    CulturalEvent,
    GuideRegistry,
    PricingBenchmark,
    Region,
    TrekkingRoute,
)
from .serializers import (
    CulturalEventSerializer,
    FairPriceQuerySerializer,
    FairPriceResultSerializer,
    GuideRegistrySerializer,
    PricingBenchmarkSerializer,
    RegionSerializer,
    TrekkingRouteSerializer,
)


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.filter(is_active=True)
    serializer_class = RegionSerializer
    permission_classes = (IsAdminOrReadOnly,)
    search_fields = ("name",)
    ordering_fields = ("name",)


class TrekkingRouteViewSet(viewsets.ModelViewSet):
    serializer_class = TrekkingRouteSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TrekkingRouteFilter
    search_fields = ("route_name", "region__name", "permits_required")
    ordering_fields = ("difficulty_level", "duration_days", "max_altitude_m", "estimated_cost_usd", "badge_points")

    def get_queryset(self):
        qs = TrekkingRoute.objects.select_related("region")
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_published=True)
        return qs


class GuideRegistryViewSet(viewsets.ModelViewSet):
    serializer_class = GuideRegistrySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = GuideRegistryFilter
    search_fields = ("guide_code", "ntb_license_no", "languages_spoken", "regions_covered")
    ordering_fields = ("average_rating", "years_experience", "total_trips_completed")

    def get_queryset(self):
        qs = GuideRegistry.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class CulturalEventViewSet(viewsets.ModelViewSet):
    queryset = CulturalEvent.objects.all()
    serializer_class = CulturalEventSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = CulturalEventFilter
    search_fields = ("festival_name", "region")
    ordering_fields = ("start_month", "year", "badge_points")

    @extend_schema(
        parameters=[OpenApiParameter("months", int, required=False, description="How many months ahead (1-12, default 6).")],
        description="Festivals grouped by month for the information-hub calendar. "
        "Starts from the current month and wraps around the year; each festival is "
        "de-duplicated across years/regions, with the regions it is celebrated in.",
    )
    @action(detail=False, methods=["get"], url_path="upcoming", permission_classes=[AllowAny])
    def upcoming(self, request, *args, **kwargs):
        try:
            months_ahead = int(request.query_params.get("months", 6))
        except (TypeError, ValueError):
            months_ahead = 6
        months_ahead = max(1, min(months_ahead, 12))

        start = date.today().month
        # The calendar only changes when events are edited; cache it briefly so
        # this scan-and-group doesn't run on every open.
        cache_key = f"events:upcoming:{start}:{months_ahead}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        wanted = [((start - 1 + i) % 12) + 1 for i in range(months_ahead)]

        buckets: dict[int, dict[str, dict]] = {m: {} for m in wanted}
        for ev in CulturalEvent.objects.filter(start_month__in=wanted):
            festivals = buckets[ev.start_month]
            fest = festivals.get(ev.festival_name)
            if fest is None:
                fest = {
                    "festival_name": ev.festival_name,
                    "event_type": ev.event_type,
                    "significance": ev.significance,
                    "duration_days": ev.duration_days,
                    "badge_eligible": ev.badge_eligible,
                    "badge_points": ev.badge_points,
                    "regions": set(),
                }
                festivals[ev.festival_name] = fest
            if ev.region:
                fest["regions"].add(ev.region)

        months = [
            {
                "month": m,
                "month_name": calendar.month_name[m],
                "festivals": [
                    {**f, "regions": sorted(f["regions"])}
                    for f in sorted(buckets[m].values(), key=lambda x: x["festival_name"])
                ],
            }
            for m in wanted
        ]
        payload = {"from_month": start, "months": months}
        cache.set(cache_key, payload, 60 * 30)  # 30 minutes
        return Response(payload)


class PricingBenchmarkViewSet(viewsets.ModelViewSet):
    queryset = PricingBenchmark.objects.select_related("region")
    serializer_class = PricingBenchmarkSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = PricingBenchmarkFilter
    search_fields = ("service_type",)
    ordering_fields = ("fair_price_npr", "last_updated")

    @extend_schema(
        parameters=[
            OpenApiParameter("service_type", str, required=True),
            OpenApiParameter("region", str, required=False),
            OpenApiParameter("season", str, required=False),
        ],
        responses=FairPriceResultSerializer,
        description="Aggregated fair-price range for a service. Powers transparent "
        "pricing and is the deterministic fallback for the anti-scam check.",
    )
    @action(detail=False, methods=["get"], url_path="lookup", permission_classes=[AllowAny])
    def lookup(self, request):
        query = FairPriceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = PricingBenchmark.fair_price_for(
            service_type=query.validated_data["service_type"],
            region_name=query.validated_data.get("region") or None,
            season=query.validated_data.get("season") or None,
        )
        if result is None:
            raise NotFound("No benchmark available for the requested service.")
        return Response(FairPriceResultSerializer(result).data)
