"""Personalised recommendation feed for tourists.

These endpoints are the app-facing front for the ML ``analytics-engine``. They
build a tourist profile from the request, ask the ML service to rank routes /
guides, then re-hydrate the ranked ids with the real catalog rows so the app gets
full cards (cost, duration, rating, ...) and not just ids and scores.

If the ML service is unreachable the views degrade to a sensible deterministic
ordering (most rewarding routes / highest-rated guides) so the feed never breaks.
"""
from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from src.catalog.models import GuideRegistry, TrekkingRoute
from src.catalog.serializers import GuideRegistrySerializer, TrekkingRouteSerializer
from src.common.services import get_analytics_client

from .serializers import (
    GuideRecommendationQuerySerializer,
    RouteRecommendationQuerySerializer,
)

# How many candidate guides we hand to the ranker. Ranking is cheap and
# transparent, so a generous shortlist keeps results relevant without a big call.
GUIDE_CANDIDATE_LIMIT = 50


class RouteRecommendationsView(APIView):
    """``GET /api/v1/recommendations/routes/`` — suggested treks for the tourist."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(parameters=[RouteRecommendationQuerySerializer])
    def get(self, request, *args, **kwargs):
        query = RouteRecommendationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        season = query.validated_data.get("season") or None
        top_k = query.validated_data["top_k"]

        ml = get_analytics_client().recommend_routes(
            tourist=query.to_tourist(), season=season, top_k=top_k
        )

        published = TrekkingRoute.objects.select_related("region").filter(is_published=True)

        if ml and ml.get("items"):
            by_id = {r.external_id: r for r in published}
            results = []
            for item in ml["items"]:
                route = by_id.get(item["route_id"])
                if route is None:
                    continue
                data = TrekkingRouteSerializer(route).data
                data["score"] = item["score"]
                data["components"] = item.get("components", {})
                results.append(data)
            if results:
                return Response(
                    {"source": "ml", "model_version": ml.get("model_version", ""), "results": results}
                )

        # Fallback — most rewarding published routes.
        routes = published.order_by("-badge_points", "-estimated_cost_usd")[:top_k]
        return Response(
            {"source": "fallback", "model_version": "", "results": TrekkingRouteSerializer(routes, many=True).data}
        )


class GuideRecommendationsView(APIView):
    """``GET /api/v1/recommendations/guides/`` — best-matched verified guides."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(parameters=[GuideRecommendationQuerySerializer])
    def get(self, request, *args, **kwargs):
        query = GuideRecommendationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        top_k = query.validated_data["top_k"]

        shortlist = list(
            GuideRegistry.objects.filter(is_active=True).order_by("-average_rating")[:GUIDE_CANDIDATE_LIMIT]
        )
        candidates = [
            {
                "guide_id": g.external_id,
                "certification": g.certification,
                "average_rating": float(g.average_rating or 0),
                "regions_covered": g.regions_covered,
                "languages_spoken": g.languages_spoken,
            }
            for g in shortlist
        ]

        ml = get_analytics_client().rank_guides(tourist=query.to_tourist(), candidates=candidates)

        if ml and ml.get("items"):
            by_id = {g.external_id: g for g in shortlist}
            results = []
            for item in ml["items"][:top_k]:
                guide = by_id.get(item.get("guide_id"))
                if guide is None:
                    continue
                data = GuideRegistrySerializer(guide).data
                data["score"] = item["score"]
                data["components"] = item.get("components", {})
                results.append(data)
            if results:
                return Response(
                    {"source": "ml", "model_version": ml.get("model_version", ""), "results": results}
                )

        # Fallback — highest-rated active guides.
        return Response(
            {"source": "fallback", "model_version": "", "results": GuideRegistrySerializer(shortlist[:top_k], many=True).data}
        )
