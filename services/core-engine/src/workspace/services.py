"""AI itinerary suggestions for a travel workspace.

Reuses the Sprint 4 recommendation pipeline: ask the analytics-engine to rank
trekking routes for the tourist, then spread the top picks across the trip's days
to seed a starter itinerary. Falls back to the most rewarding published routes if
the ML service is unavailable, so "Suggest my trip" always returns something.
"""
from __future__ import annotations

from decimal import Decimal

from src.catalog.models import TrekkingRoute
from src.common.services import get_analytics_client

from .models import TravelWorkspace, WorkspaceItem

# Rough NPR per USD, only to turn the dataset's USD route cost into an NPR
# estimate for the budget tracker. The tourist edits costs anyway.
_NPR_PER_USD = 134
_DEFAULT_ITEM_COST_NPR = Decimal("3000.00")


def _estimate_cost_npr(route: TrekkingRoute) -> Decimal:
    if route.estimated_cost_usd:
        return Decimal(route.estimated_cost_usd * _NPR_PER_USD)
    return _DEFAULT_ITEM_COST_NPR


def suggest_itinerary(workspace: TravelWorkspace, *, adventure: float = 0.6, season: str | None = None) -> list[dict]:
    """Build a preview itinerary (does not save anything)."""
    trip_days = workspace.trip_days
    tourist = {"pref_adventure_score": adventure, "pref_culture_score": 0.5, "pref_nature_score": 0.6}

    ml = get_analytics_client().recommend_routes(tourist=tourist, season=season, top_k=min(trip_days, 8))
    published = TrekkingRoute.objects.filter(is_published=True)

    routes: list[TrekkingRoute] = []
    if ml and ml.get("items"):
        by_id = {r.external_id: r for r in published}
        routes = [by_id[i["route_id"]] for i in ml["items"] if i["route_id"] in by_id]
    if not routes:
        routes = list(published.order_by("-badge_points")[: min(trip_days, 8)])

    suggestions = []
    for day, route in enumerate(routes[:trip_days], start=1):
        suggestions.append(
            {
                "day_number": day,
                "route_id": route.id,
                "route_external_id": route.external_id,
                "title": f"Explore {route.route_name}",
                "region": route.region.name,
                "difficulty": route.difficulty,
                "estimated_cost_npr": float(_estimate_cost_npr(route)),
            }
        )
    return suggestions


def apply_itinerary(workspace: TravelWorkspace, **kwargs) -> list[WorkspaceItem]:
    """Generate suggestions and save them as workspace items."""
    suggestions = suggest_itinerary(workspace, **kwargs)
    items = [
        WorkspaceItem(
            workspace=workspace,
            item_type=WorkspaceItem.ItemType.DESTINATION,
            route_id=s["route_id"],
            day_number=s["day_number"],
            custom_title=s["title"],
            estimated_cost_npr=Decimal(str(s["estimated_cost_npr"])),
        )
        for s in suggestions
    ]
    return WorkspaceItem.objects.bulk_create(items)
