"""Travel workspace — a tourist's personal trip planner.

A workspace is one trip ("Annapurna 2026"); its items are the day-by-day plan
(a route to visit, a guide to hire, a package, or a custom activity). Drag-and-
drop in the app reorders items by ``day_number`` + ``display_order``. Budgeting
compares the trip budget against the sum of the items' estimated costs.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from src.common.models import TimeStampedModel


class TravelWorkspace(TimeStampedModel):
    tourist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspaces", db_index=True
    )
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget_npr = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency_preference = models.CharField(max_length=3, default="NPR")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.title} ({self.tourist_id})"

    @property
    def total_planned_cost_npr(self) -> Decimal:
        return sum((item.estimated_cost_npr for item in self.items.all()), Decimal("0.00"))

    @property
    def trip_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class WorkspaceItem(TimeStampedModel):
    class ItemType(models.TextChoices):
        DESTINATION = "destination", "Destination Visit"
        GUIDE = "guide", "Guide"
        PACKAGE = "package", "Tour Package"
        CUSTOM = "custom", "Custom Activity"
        ACCOMMODATION = "accommodation", "Accommodation"
        TRANSPORT = "transport", "Transport"

    workspace = models.ForeignKey(TravelWorkspace, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=ItemType.choices)

    # Linked catalog entities — only the one matching item_type is set.
    route = models.ForeignKey(
        "catalog.TrekkingRoute", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    guide = models.ForeignKey(
        "catalog.GuideRegistry", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    package = models.ForeignKey(
        "bookings.TourPackage", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    custom_title = models.CharField(max_length=255, blank=True)
    custom_description = models.TextField(blank=True)

    day_number = models.PositiveSmallIntegerField(default=1)
    display_order = models.PositiveSmallIntegerField(default=0)
    start_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    estimated_cost_npr = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["day_number", "display_order"]
        indexes = [models.Index(fields=["workspace", "day_number", "display_order"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Day {self.day_number}: {self.custom_title or self.item_type}"

    @property
    def title(self) -> str:
        """A readable label regardless of item type."""
        if self.custom_title:
            return self.custom_title
        if self.route_id and self.route:
            return self.route.route_name
        if self.guide_id and self.guide:
            return self.guide.guide_code
        if self.package_id and self.package:
            return self.package.title
        return self.get_item_type_display()
