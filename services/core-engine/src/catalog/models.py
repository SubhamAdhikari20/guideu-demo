"""Tourism catalog — the reference domain mirrored from the synthetic dataset.

Maps the dataset's reference tables onto first-class Django models:

* ``trekking_routes.csv``     -> :class:`TrekkingRoute`
* ``verified_guides.csv``     -> :class:`GuideRegistry`
* ``cultural_events.csv``     -> :class:`CulturalEvent`
* ``pricing_benchmarks.csv``  -> :class:`PricingBenchmark`
* the 15 trek regions         -> :class:`Region`

Each row carries an ``external_id`` (the dataset PK, e.g. ``RTE0001``) so the
ingestion command is idempotent and ML feature joins remain stable.
"""
from __future__ import annotations

from django.db import models
from django.db.models import Avg
from django.utils.text import slugify

from src.common.models import TimeStampedModel


class Region(TimeStampedModel):
    """A Nepal trekking region (the 15-value vocabulary used by routes/pricing)."""

    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_remote = models.BooleanField(
        default=False, help_text="Remote regions carry a pricing premium (Dolpo, Mustang, ...)."
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:80]
        super().save(*args, **kwargs)


class Difficulty(models.TextChoices):
    EASY = "Easy", "Easy"
    MODERATE = "Moderate", "Moderate"
    HARD = "Hard", "Hard"
    VERY_HARD = "Very Hard", "Very Hard"


class TrekkingRoute(TimeStampedModel):
    """A trekking route — maps ``trekking_routes.csv``."""

    external_id = models.CharField(max_length=16, unique=True, db_index=True, help_text="Dataset route_id, e.g. RTE0001")
    route_name = models.CharField(max_length=255, db_index=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="routes")
    permits_required = models.CharField(max_length=255, blank=True, help_text="Comma-separated permit names")
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices, db_index=True)
    difficulty_level = models.PositiveSmallIntegerField(default=1, help_text="1=Easy .. 4=Very Hard")
    max_altitude_m = models.PositiveIntegerField(default=0)
    duration_days = models.PositiveSmallIntegerField(default=1)
    best_seasons = models.CharField(max_length=64, blank=True)
    seasonal_closure_months = models.CharField(max_length=64, blank=True)
    badge_points = models.PositiveIntegerField(default=0)
    estimated_cost_usd = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True, db_index=True, help_text="Moderation gate")

    class Meta:
        ordering = ["route_name"]
        indexes = [
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["region", "difficulty_level"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.route_name

    @property
    def permit_list(self) -> list[str]:
        return [p.strip() for p in self.permits_required.split(",") if p.strip()]

    @property
    def best_season_list(self) -> list[str]:
        return [s.strip() for s in self.best_seasons.split(",") if s.strip()]


class Certification(models.TextChoices):
    IFMGA = "IFMGA Mountain Guide", "IFMGA Mountain Guide"
    GOVT_TREK = "Government Trekking Guide", "Government Trekking Guide"
    NATHM_TREK = "NATHM Trekking Guide", "NATHM Trekking Guide"
    NATHM_TOUR = "NATHM Tour Guide", "NATHM Tour Guide"
    CITY = "City Guide (Licensed)", "City Guide (Licensed)"
    CULTURAL = "Cultural Specialist", "Cultural Specialist"
    BIRD = "Bird-watching Specialist", "Bird-watching Specialist"
    ADVENTURE = "Adventure Sports Guide", "Adventure Sports Guide"


class VerificationStatus(models.TextChoices):
    VERIFIED = "Verified", "Verified"
    PENDING = "Pending Renewal", "Pending Renewal"
    EXPIRED = "Expired", "Expired"


class GuideRegistry(TimeStampedModel):
    """NTB-registered guide — reference registry from ``verified_guides.csv``.

    This is the *licensing registry* (who is licensed in Nepal), distinct from
    ``authentication.GuideProfile`` (who has signed up to GuideU). When an app
    guide is verified against a registry row, ``linked_profile`` is set.
    """

    external_id = models.CharField(max_length=16, unique=True, db_index=True, help_text="Dataset guide_id, e.g. GDE00001")
    guide_code = models.CharField(max_length=64, db_index=True, help_text="Public code shown in-app")
    ntb_license_no = models.CharField(max_length=64, db_index=True)
    certification = models.CharField(max_length=64, choices=Certification.choices, db_index=True)
    languages_spoken = models.CharField(max_length=255, blank=True)
    regions_covered = models.CharField(max_length=512, blank=True, help_text="Comma-separated region names")
    years_experience = models.FloatField(default=0)
    average_rating = models.FloatField(default=0, db_index=True)
    total_trips_completed = models.PositiveIntegerField(default=0)
    verification_status = models.CharField(
        max_length=32, choices=VerificationStatus.choices, default=VerificationStatus.VERIFIED, db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    linked_profile = models.OneToOneField(
        "authentication.GuideProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registry_entry",
    )

    class Meta:
        ordering = ["-average_rating"]
        verbose_name = "guide registry entry"
        verbose_name_plural = "guide registry"
        indexes = [models.Index(fields=["certification", "average_rating"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.guide_code} ({self.certification})"

    @property
    def language_list(self) -> list[str]:
        return [s.strip() for s in self.languages_spoken.split(",") if s.strip()]

    @property
    def region_list(self) -> list[str]:
        return [s.strip() for s in self.regions_covered.split(",") if s.strip()]

    @property
    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED


class EventType(models.TextChoices):
    RELIGIOUS = "Religious", "Religious"
    CULTURAL = "Cultural", "Cultural"
    SEASONAL = "Seasonal", "Seasonal"


class Significance(models.TextChoices):
    HIGH = "High", "High"
    MEDIUM = "Medium", "Medium"
    LOW = "Low", "Low"


class CulturalEvent(TimeStampedModel):
    """A festival occurrence — maps ``cultural_events.csv``.

    ``region`` here uses the *province* vocabulary (Bagmati, Gandaki, ...), which
    differs from the trek :class:`Region` set, so it is stored as free text.
    """

    external_id = models.CharField(max_length=16, unique=True, db_index=True)
    festival_name = models.CharField(max_length=128, db_index=True)
    event_type = models.CharField(max_length=16, choices=EventType.choices, db_index=True)
    start_month = models.PositiveSmallIntegerField(default=1)
    duration_days = models.PositiveSmallIntegerField(default=1)
    region = models.CharField(max_length=128, blank=True, help_text="Province/area name (free text)")
    year = models.PositiveSmallIntegerField(db_index=True)
    badge_eligible = models.BooleanField(default=False)
    significance = models.CharField(max_length=8, choices=Significance.choices, default=Significance.MEDIUM)
    badge_points = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["start_month", "festival_name"]
        indexes = [models.Index(fields=["year", "start_month"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.festival_name} {self.year}"


class PricingBenchmark(TimeStampedModel):
    """Fair-price benchmark sample — maps ``pricing_benchmarks.csv``.

    The anti-scam ground truth. Rows are samples per (service, region, season);
    :meth:`fair_price_for` aggregates them for a benchmark lookup.
    """

    external_id = models.CharField(max_length=16, unique=True, db_index=True)
    service_type = models.CharField(max_length=64, db_index=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="benchmarks")
    season = models.CharField(max_length=32, db_index=True, help_text="Peak (Spring) / Off (Winter) / ...")
    fair_price_npr = models.PositiveIntegerField()
    min_fair_npr = models.PositiveIntegerField()
    max_fair_npr = models.PositiveIntegerField()
    currency = models.CharField(max_length=8, default="NPR")
    unit = models.CharField(max_length=32, blank=True)
    source_type = models.CharField(max_length=32, blank=True)
    last_updated = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["service_type", "region__name"]
        indexes = [models.Index(fields=["service_type", "region", "season"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.service_type} @ {self.region_id} ({self.season}): {self.fair_price_npr} NPR"

    @classmethod
    def resolve_region_name(cls, region_name: str | None) -> str | None:
        """Map a caller's region string onto the canonical 15-value vocabulary.

        The dataset writes compound names like ``Everest/Khumbu``, but clients
        and reports commonly say just ``Everest``. Without this, an alias looks
        like an unknown region and the price check silently returns nothing.
        """
        if not region_name:
            return None
        wanted = region_name.strip()
        if not wanted:
            return None
        names = list(Region.objects.values_list("name", flat=True))
        lowered = wanted.casefold()
        for name in names:
            if name.casefold() == lowered:
                return name
        # "Everest" -> "Everest/Khumbu", "Khumbu" -> "Everest/Khumbu"
        for name in names:
            if any(part.strip().casefold() == lowered for part in name.split("/")):
                return name
        return None

    @classmethod
    def fair_price_for(cls, *, service_type: str, region_name: str | None = None, season: str | None = None) -> dict | None:
        """Aggregate a fair-price range for a (service, region, season).

        Falls back progressively — (service, region, season) -> (service,
        region) -> (service) — so a caller who names an unknown region or an
        out-of-vocabulary season still gets the national benchmark instead of
        nothing. The returned ``granularity`` says which level answered, which
        matches what the analytics-engine reports for the same lookup.

        Returns ``None`` only when the service itself has no benchmark sample.
        """
        base = cls.objects.filter(service_type__iexact=service_type)
        canonical_region = cls.resolve_region_name(region_name)

        attempts: list[tuple[str, str | None, str | None]] = []
        if canonical_region and season:
            attempts.append(("service+region+season", canonical_region, season))
        if canonical_region:
            attempts.append(("service+region", canonical_region, None))
        attempts.append(("service", None, None))

        for granularity, region_filter, season_filter in attempts:
            qs = base
            if region_filter:
                qs = qs.filter(region__name__iexact=region_filter)
            if season_filter:
                qs = qs.filter(season__iexact=season_filter)
            agg = qs.aggregate(fair=Avg("fair_price_npr"), low=Avg("min_fair_npr"), high=Avg("max_fair_npr"))
            if agg["fair"] is None:
                continue
            return {
                "service_type": service_type,
                "region": region_filter,
                "season": season_filter,
                "fair_price_npr": round(agg["fair"]),
                "min_fair_npr": round(agg["low"]),
                "max_fair_npr": round(agg["high"]),
                "currency": "NPR",
                "sample_size": qs.count(),
                "granularity": granularity,
            }
        return None
