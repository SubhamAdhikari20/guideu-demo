"""Ingest the Travel Planning synthetic dataset into the core engine.

Idempotent, chunked bulk load of the reference catalog (regions, routes, guide
registry, cultural events, pricing benchmarks) plus the badge catalog. Keyed on
each row's ``external_id`` so re-running is safe (conflicts are ignored).

Usage::

    python manage.py seed_from_dataset --dataset-dir "../../../Travel Planning"
    python manage.py seed_from_dataset --flush            # wipe catalog first
    python manage.py seed_from_dataset --with-demo-bookings

Transactional tables (bookings/interactions/scam reports) intentionally stay in
the dataset for ML training in the analytics-engine; ``--with-demo-bookings``
materialises a small demo slice so the booking flow is explorable.
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Iterable, Iterator

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.catalog.models import (
    CulturalEvent,
    GuideRegistry,
    PricingBenchmark,
    Region,
    TrekkingRoute,
)

# The 15 canonical trek regions and the remote-premium subset (from the
# dataset generator's REGIONS / remote multiplier).
CANONICAL_REGIONS = [
    "Kathmandu Valley", "Pokhara/Annapurna", "Everest/Khumbu", "Langtang", "Mustang",
    "Manaslu", "Chitwan/Terai", "Lumbini", "Janakpur", "Kanchenjunga", "Makalu",
    "Dolpo", "Rara/Karnali", "Helambu", "Bandipur/Gandaki",
]
REMOTE_REGIONS = {"Dolpo", "Mustang", "Manaslu", "Kanchenjunga", "Makalu", "Rara/Karnali"}

# Badge catalog (mirrors the dataset generator's BADGES) so gamification has
# reference data to award against.
BADGES = [
    ("Culture Explorer", "Cultural", 80, "Attended Festival"),
    ("Festival Photographer", "Cultural", 120, "Posted Festival Photos"),
    ("Heritage Walker", "Cultural", 60, "Completed Heritage Tour"),
    ("Pilgrim", "Cultural", 100, "Visited Sacred Site"),
    ("Trail Starter", "Adventure", 50, "Completed First Trek"),
    ("Altitude Achiever", "Adventure", 200, "Crossed 4000m"),
    ("High Altitude Hero", "Adventure", 350, "Crossed 5000m"),
    ("Snow Leopard", "Adventure", 500, "Crossed 5500m"),
    ("Eco Trekker", "Explorer", 90, "Followed Leave-No-Trace"),
    ("Local Friend", "Explorer", 70, "Stayed in Homestay"),
    ("Multi-Region Explorer", "Explorer", 150, "Visited 3+ Regions"),
    ("Safety First", "Safety", 60, "Hired Verified Guide"),
    ("Scam Spotter", "Safety", 80, "Reported Verified Scam"),
    ("Fair Pay Advocate", "Safety", 50, "Paid Within Benchmark"),
    ("Wellness Wanderer", "Cultural", 60, "Completed Yoga Retreat"),
    ("Wildlife Witness", "Adventure", 90, "Wildlife Safari Completed"),
]


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _to_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def _read_csv(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def _chunked(iterable: Iterable, size: int) -> Iterator[list]:
    batch: list = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


class Command(BaseCommand):
    help = "Ingest the Travel Planning synthetic dataset into the core catalog."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dataset-dir",
            default="",
            help="Path to the Travel Planning dataset directory (auto-discovered when omitted).",
        )
        parser.add_argument("--flush", action="store_true", help="Delete existing catalog rows first.")
        parser.add_argument("--max-pricing", type=int, default=0, help="Cap pricing rows for fast dev seeds (0 = all).")
        parser.add_argument("--with-demo-bookings", action="store_true", help="Also create a small demo booking slice.")
        parser.add_argument("--batch-size", type=int, default=2000)

    def handle(self, *args, **options) -> None:
        dataset_dir = self._resolve_dataset_dir(options["dataset_dir"])
        if dataset_dir is None:
            raise CommandError(
                "Dataset directory not found. Pass --dataset-dir or set GUIDEU_DATASET_DIR. "
                "The Travel Planning package usually sits next to the guideu repo."
            )
        self.stdout.write(f"Using dataset: {dataset_dir}")

        self.batch_size = options["batch_size"]
        if options["flush"]:
            self._flush()

        region_cache = self._seed_regions()
        self._seed_routes(dataset_dir / "trekking_routes.csv", region_cache)
        self._seed_guides(dataset_dir / "verified_guides.csv")
        self._seed_events(dataset_dir / "cultural_events.csv")
        self._seed_pricing(dataset_dir / "pricing_benchmarks.csv", region_cache, options["max_pricing"])
        self._seed_badges()

        if options["with_demo_bookings"]:
            self._seed_demo_bookings()

        self.stdout.write(self.style.SUCCESS("Dataset ingestion complete."))

    # ---- path resolution ---------------------------------------------------
    def _resolve_dataset_dir(self, explicit: str) -> Path | None:
        """Find the dataset directory, trying the arg, env, then known locations."""
        import os

        from django.conf import settings

        candidates: list[Path] = []
        if explicit:
            candidates.append(Path(explicit).expanduser())
        env = os.environ.get("GUIDEU_DATASET_DIR")
        if env:
            candidates.append(Path(env).expanduser())
        base = Path(settings.BASE_DIR)  # .../Project/guideu/services/core-engine
        candidates += [
            base.parent.parent.parent / "Travel Planning",     # Project/Travel Planning (repo sibling)
            base.parent.parent / "Travel Planning",            # guideu/Travel Planning (if vendored in)
            Path.cwd() / "Travel Planning",
        ]
        for candidate in candidates:
            if (candidate / "trekking_routes.csv").exists():
                return candidate.resolve()
        return None

    # ---- steps -------------------------------------------------------------
    def _flush(self) -> None:
        self.stdout.write("Flushing existing catalog rows ...")
        PricingBenchmark.objects.all().delete()
        TrekkingRoute.objects.all().delete()
        CulturalEvent.objects.all().delete()
        GuideRegistry.objects.all().delete()
        Region.objects.all().delete()

    def _seed_regions(self) -> dict[str, Region]:
        for name in CANONICAL_REGIONS:
            Region.objects.update_or_create(
                name=name, defaults={"is_remote": name in REMOTE_REGIONS, "is_active": True}
            )
        cache = {r.name: r for r in Region.objects.all()}
        self.stdout.write(self.style.SUCCESS(f"Regions: {len(cache)}"))
        return cache

    def _region_for(self, name: str, cache: dict[str, Region]) -> Region:
        name = (name or "").strip()
        if name not in cache:
            cache[name] = Region.objects.create(name=name, is_remote=name in REMOTE_REGIONS)
        return cache[name]

    def _seed_routes(self, path: Path, region_cache: dict[str, Region]) -> None:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"skip routes (missing {path.name})"))
            return
        objects = (
            TrekkingRoute(
                external_id=row["route_id"],
                route_name=row["route_name"],
                region=self._region_for(row["region"], region_cache),
                permits_required=row.get("permits_required", ""),
                difficulty=row.get("difficulty", ""),
                difficulty_level=int(row.get("difficulty_level") or 1),
                max_altitude_m=int(row.get("max_altitude_m") or 0),
                duration_days=int(row.get("duration_days") or 1),
                best_seasons=row.get("best_seasons", ""),
                seasonal_closure_months=row.get("seasonal_closure_months", ""),
                badge_points=int(row.get("badge_points") or 0),
                estimated_cost_usd=int(row.get("estimated_cost_usd") or 0),
            )
            for row in _read_csv(path)
        )
        self._bulk(TrekkingRoute, objects, "Routes")

    def _seed_guides(self, path: Path) -> None:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"skip guides (missing {path.name})"))
            return
        objects = (
            GuideRegistry(
                external_id=row["guide_id"],
                guide_code=row.get("guide_code", ""),
                ntb_license_no=row.get("ntb_license_no", ""),
                certification=row.get("certification", ""),
                languages_spoken=row.get("languages_spoken", ""),
                regions_covered=row.get("regions_covered", ""),
                years_experience=float(row.get("years_experience") or 0),
                average_rating=float(row.get("average_rating") or 0),
                total_trips_completed=int(row.get("total_trips_completed") or 0),
                verification_status=row.get("verification_status", "Verified"),
                is_active=_to_bool(row.get("is_active", "True")),
            )
            for row in _read_csv(path)
        )
        self._bulk(GuideRegistry, objects, "Guides")

    def _seed_events(self, path: Path) -> None:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"skip events (missing {path.name})"))
            return
        objects = (
            CulturalEvent(
                external_id=row["event_id"],
                festival_name=row.get("festival_name", ""),
                event_type=row.get("event_type", "Cultural"),
                start_month=int(row.get("start_month") or 1),
                duration_days=int(row.get("duration_days") or 1),
                region=row.get("region", ""),
                year=int(row.get("year") or 2024),
                badge_eligible=_to_bool(row.get("badge_eligible", "False")),
                significance=row.get("significance", "Medium"),
                badge_points=int(row.get("badge_points") or 0),
            )
            for row in _read_csv(path)
        )
        self._bulk(CulturalEvent, objects, "Events")

    def _seed_pricing(self, path: Path, region_cache: dict[str, Region], max_rows: int) -> None:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"skip pricing (missing {path.name})"))
            return

        def rows() -> Iterator[PricingBenchmark]:
            for i, row in enumerate(_read_csv(path)):
                if max_rows and i >= max_rows:
                    break
                yield PricingBenchmark(
                    external_id=row["benchmark_id"],
                    service_type=row.get("service_type", ""),
                    region=self._region_for(row["region"], region_cache),
                    season=row.get("season", ""),
                    fair_price_npr=int(row.get("fair_price_npr") or 0),
                    min_fair_npr=int(row.get("min_fair_npr") or 0),
                    max_fair_npr=int(row.get("max_fair_npr") or 0),
                    currency=row.get("currency", "NPR"),
                    unit=row.get("unit", ""),
                    source_type=row.get("source_type", ""),
                    last_updated=_to_date(row.get("last_updated", "")),
                )

        self._bulk(PricingBenchmark, rows(), "Pricing benchmarks")

    def _seed_badges(self) -> None:
        from src.gamification.models import Badge

        for name, category, points, trigger in BADGES:
            Badge.objects.update_or_create(
                name=name, defaults={"category": category, "points": points, "trigger_event": trigger}
            )
        self.stdout.write(self.style.SUCCESS(f"Badges: {Badge.objects.count()}"))

    def _seed_demo_bookings(self) -> None:
        """Create a small, explorable booking slice (demo users + bookings)."""
        from django.contrib.auth import get_user_model

        from src.bookings.models import BookingSession, TourPackage

        User = get_user_model()
        package, _ = TourPackage.objects.get_or_create(
            title="Custom Guided Trek",
            defaults={"description": "Flexible guided trek package.", "base_price": 1200, "duration_days": 10, "capacity": 8},
        )
        routes = list(TrekkingRoute.objects.all()[:10])
        if not routes:
            self.stdout.write(self.style.WARNING("no routes loaded; skipping demo bookings"))
            return

        created = 0
        for i in range(10):
            tourist, _ = User.objects.get_or_create(
                username=f"demo_tourist_{i}",
                defaults={"email": f"demo_tourist_{i}@example.com", "role": User.Roles.TOURIST},
            )
            route = routes[i % len(routes)]
            start = dt.date.today() + dt.timedelta(days=14 + i)
            end = start + dt.timedelta(days=route.duration_days)
            BookingSession.objects.get_or_create(
                booking_reference=f"DEMO{i:06d}",
                defaults={
                    "tourist": tourist,
                    "tour_package": package,
                    "route": route,
                    "start_date": start,
                    "end_date": end,
                    "total_price": route.estimated_cost_usd,
                    "status": BookingSession.Status.CONFIRMED,
                },
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Demo bookings: {created}"))

    # ---- helpers -----------------------------------------------------------
    def _bulk(self, model, objects: Iterator, label: str) -> None:
        total = 0
        with transaction.atomic():
            for batch in _chunked(objects, self.batch_size):
                model.objects.bulk_create(batch, batch_size=self.batch_size, ignore_conflicts=True)
                total += len(batch)
        self.stdout.write(self.style.SUCCESS(f"{label}: {total} rows processed"))
