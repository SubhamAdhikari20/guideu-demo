"""Safety SOS alerts.

A tourist (or, later, an IoT trekking wearable) raises an SOS with their last
known location. The record is the source of truth a responder / admin acts on.
The same endpoint is device-ready: a wearable can POST the same payload with the
owner's token, so no model change is needed to add real hardware later.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from src.common.models import TimeStampedModel


class SosAlert(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RESOLVED = "RESOLVED", "Resolved"
        CANCELLED = "CANCELLED", "Cancelled"

    class Source(models.TextChoices):
        APP = "APP", "Mobile app"
        DEVICE = "DEVICE", "IoT device"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sos_alerts", db_index=True
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    message = models.TextField(blank=True)
    source = models.CharField(max_length=8, choices=Source.choices, default=Source.APP)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"SOS {self.user_id} ({self.status})"

    def resolve(self) -> None:
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])
