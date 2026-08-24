"""Ingest the Travel Planning synthetic dataset into the core engine.

Idempotent, chunked bulk load of the reference catalog (regions, routes, guide
registry, cultural events, pricing benchmarks) plus the badge catalog. Keyed on
each row's ``external_id`` so re-running is safe (conflicts are ignored).

Usage::

    python manage.py seed_from_dataset --dataset-dir "../../../Travel Planning"
    python manage.py seed_from_dataset --flush            # wipe catalog first
    python manage.py seed_from_dataset --with-demo-bookings
    python manage.py seed_from_dataset --with-demo-scam-reports

Transactional tables (bookings/interactions/scam reports) intentionally stay in
the dataset for ML training in the analytics-engine; ``--with-demo-bookings``
and ``--with-demo-scam-reports`` materialise small demo slices so the booking
flow and the moderation queue are explorable.
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
# Passwords for the seeded demo accounts. Local demonstration logins against a
# synthetic dataset — a real deployment seeds nothing, so these never exist
# outside a developer machine. Kept here so the docs and the seeder cannot
# drift apart. The admin password is the one already documented in the run and
# demo guides; do not change it without updating both.
DEMO_PASSWORD = "TouristDemo123!"
DEMO_PASSWORDS = {
    "tourist@guideu.local": "TouristDemo123!",
    "guide@guideu.local": "GuideDemo123!",
    "admin@guideu.local": "AdminDemo123!",
}

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
        parser.add_argument(
            "--with-demo-accounts",
            action="store_true",
            help="Create the named tourist/guide/admin demo logins used in the demonstration.",
        )
        parser.add_argument(
            "--with-demo-scam-reports",
            action="store_true",
            help="Also import a small slice of scam_reports.csv so the moderation queue is not empty.",
        )
        parser.add_argument("--batch-size", type=int, default=2000)

    def handle(self, *args, **options) -> None:
        # Historical seed rows are not live domain events. Suppressing fan-out
        # also keeps a bare local seed fast when Redis is intentionally absent.
        from django.conf import settings
        settings.EVENTS_ENABLED = False
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

        # Before bookings: the demo guide has to exist to be assignable.
        if options["with_demo_accounts"]:
            self._seed_demo_accounts()
            self._seed_demo_travel_inventory()

        if options["with_demo_bookings"]:
            self._seed_demo_bookings()

        if options["with_demo_scam_reports"]:
            self._seed_demo_scam_reports(dataset_dir / "scam_reports.csv", region_cache)

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

    def _seed_demo_accounts(self) -> None:
        """Create the named logins the demonstration script signs in with.

        The app has no seeded identity otherwise: the tourists attached to demo
        bookings are created by ``get_or_create``, which does not hash a
        password, so they exist but cannot log in. These three are created
        properly and are the ones documented in the demo guide.

        Roles matter beyond a badge — ``role=GUIDE`` is what makes a user
        assignable as a booking's guide (``bookings.models``) and is what
        ``IsVerifiedGuide`` checks — so the guide account is created with the
        role set at creation time, which is also when the profile signal fires.
        """
        from django.contrib.auth import get_user_model

        from src.authentication.models import GuideProfile

        User = get_user_model()
        accounts = [
            {
                "username": "demo_tourist", "email": "tourist@guideu.local",
                "role": User.Roles.TOURIST, "first_name": "Asha", "last_name": "Gurung",
                "nationality": "Nepal", "phone_number": "+977-9800000001",
            },
            {
                "username": "demo_guide", "email": "guide@guideu.local",
                "role": User.Roles.GUIDE, "first_name": "Pemba", "last_name": "Sherpa",
                "nationality": "Nepal", "phone_number": "+977-9800000002",
                "is_guide_verified": True,
            },
            {
                "username": "demo_admin", "email": "admin@guideu.local",
                "role": User.Roles.ADMIN, "first_name": "GuideU", "last_name": "Admin",
                "is_staff": True, "is_superuser": True,
            },
        ]

        for spec in accounts:
            email = spec.pop("email")
            username = spec.pop("username")
            user, created = User.objects.get_or_create(
                email=email, defaults={"username": username, **spec}
            )
            # Re-running must repair an account rather than skip it: an admin
            # made by hand earlier keeps the default TOURIST role otherwise.
            for field, value in spec.items():
                setattr(user, field, value)
            user.set_password(DEMO_PASSWORDS[email])
            user.save()
            if user.role == User.Roles.GUIDE:
                profile, _ = GuideProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "license_number": "TG-DEMO-0001",
                        "bio": "Demonstration guide account. Everest and Langtang regions.",
                        "service_areas": ["Everest/Khumbu", "Langtang"],
                    },
                )
                profile.license_number = profile.license_number or "TG-DEMO-0001"
                profile.bio = profile.bio or "Demonstration guide account. Everest and Langtang regions."
                profile.service_areas = profile.service_areas or ["Everest/Khumbu", "Langtang"]
                profile.availability = GuideProfile.Availability.AVAILABLE
                profile.daily_rate_npr = 4500
                profile.save()
            self.stdout.write(
                f"    {email:24s} {user.role:8s} {DEMO_PASSWORDS[email]:18s}"
                f" ({'created' if created else 'updated'})"
            )

        self.stdout.write(self.style.SUCCESS(f"Demo accounts: {len(accounts)}"))

    def _seed_demo_travel_inventory(self) -> None:
        """Create a small, idempotent local marketplace for all three booking types."""
        from src.bookings.models import TravelOffering

        now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
        rows = [
            {
                "service_type": "HOTEL", "provider_name": "Himalayan Heritage Hotels",
                "title": "Thamel Heritage Inn", "location": "Kathmandu",
                "unit_price": 4800, "capacity": 18, "amenities": ["Wi-Fi", "Breakfast", "Airport pickup"],
            },
            {
                "service_type": "HOTEL", "provider_name": "Lakeside Stays",
                "title": "Phewa Lake View Hotel", "location": "Pokhara",
                "unit_price": 6200, "capacity": 14, "amenities": ["Lake view", "Breakfast", "Tour desk"],
            },
            {
                "service_type": "FLIGHT", "provider_name": "Buddha Air Demo",
                "title": "Kathmandu to Pokhara Morning", "origin": "Kathmandu", "destination": "Pokhara",
                "departure_at": now + dt.timedelta(days=3, hours=2), "arrival_at": now + dt.timedelta(days=3, hours=3),
                "unit_price": 7200, "capacity": 72,
            },
            {
                "service_type": "FLIGHT", "provider_name": "Yeti Airlines Demo",
                "title": "Kathmandu to Bharatpur", "origin": "Kathmandu", "destination": "Bharatpur",
                "departure_at": now + dt.timedelta(days=4, hours=4), "arrival_at": now + dt.timedelta(days=4, hours=5),
                "unit_price": 6100, "capacity": 60,
            },
            {
                "service_type": "BUS", "provider_name": "Greenline Demo",
                "title": "Kathmandu to Pokhara Tourist Bus", "origin": "Kathmandu", "destination": "Pokhara",
                "departure_at": now + dt.timedelta(days=2, hours=1), "arrival_at": now + dt.timedelta(days=2, hours=9),
                "unit_price": 1800, "capacity": 36,
            },
            {
                "service_type": "BUS", "provider_name": "Jagadamba Demo",
                "title": "Kathmandu to Chitwan Deluxe", "origin": "Kathmandu", "destination": "Chitwan",
                "departure_at": now + dt.timedelta(days=2, hours=2), "arrival_at": now + dt.timedelta(days=2, hours=8),
                "unit_price": 1450, "capacity": 40,
            },
            # Wider inventory so each tab looks like a real listing rather than
            # two rows, and so the search and filter controls have something to
            # actually narrow down.
            {
                "service_type": "HOTEL", "provider_name": "Sherpa Hospitality",
                "title": "Namche Bazaar Lodge", "location": "Solukhumbu",
                "unit_price": 3600, "capacity": 12, "amenities": ["Heating", "Hot shower", "Drying room"],
            },
            {
                "service_type": "HOTEL", "provider_name": "Annapurna Rooms",
                "title": "Ghandruk Stone House", "location": "Kaski",
                "unit_price": 2900, "capacity": 10, "amenities": ["Mountain view", "Breakfast"],
            },
            {
                "service_type": "HOTEL", "provider_name": "Chitwan Jungle Resorts",
                "title": "Sauraha Riverside Resort", "location": "Chitwan",
                "unit_price": 5400, "capacity": 20, "amenities": ["Safari desk", "Breakfast", "Pool"],
            },
            {
                "service_type": "HOTEL", "provider_name": "Lumbini Garden Stays",
                "title": "Lumbini Peace Garden Hotel", "location": "Rupandehi",
                "unit_price": 3300, "capacity": 16, "amenities": ["Garden", "Breakfast", "Bicycle hire"],
            },
            {
                "service_type": "FLIGHT", "provider_name": "Tara Air Demo",
                "title": "Pokhara to Jomsom Early", "origin": "Pokhara", "destination": "Jomsom",
                "departure_at": now + dt.timedelta(days=5, hours=1), "arrival_at": now + dt.timedelta(days=5, hours=2),
                "unit_price": 12500, "capacity": 18,
            },
            {
                "service_type": "FLIGHT", "provider_name": "Summit Air Demo",
                "title": "Kathmandu to Lukla", "origin": "Kathmandu", "destination": "Lukla",
                "departure_at": now + dt.timedelta(days=6, hours=1), "arrival_at": now + dt.timedelta(days=6, hours=2),
                "unit_price": 21500, "capacity": 16,
            },
            {
                "service_type": "FLIGHT", "provider_name": "Shree Airlines Demo",
                "title": "Kathmandu to Biratnagar", "origin": "Kathmandu", "destination": "Biratnagar",
                "departure_at": now + dt.timedelta(days=4, hours=7), "arrival_at": now + dt.timedelta(days=4, hours=8),
                "unit_price": 8400, "capacity": 66,
            },
            {
                "service_type": "BUS", "provider_name": "Mountain Overland Demo",
                "title": "Pokhara to Kathmandu Night Coach", "origin": "Pokhara", "destination": "Kathmandu",
                "departure_at": now + dt.timedelta(days=3, hours=13), "arrival_at": now + dt.timedelta(days=3, hours=21),
                "unit_price": 1600, "capacity": 34,
            },
            {
                "service_type": "BUS", "provider_name": "Sajha Yatayat Demo",
                "title": "Kathmandu to Lumbini", "origin": "Kathmandu", "destination": "Lumbini",
                "departure_at": now + dt.timedelta(days=5, hours=2), "arrival_at": now + dt.timedelta(days=5, hours=11),
                "unit_price": 1750, "capacity": 42,
            },
            {
                "service_type": "BUS", "provider_name": "Baba Adventure Demo",
                "title": "Kathmandu to Besisahar", "origin": "Kathmandu", "destination": "Lamjung",
                "departure_at": now + dt.timedelta(days=2, hours=5), "arrival_at": now + dt.timedelta(days=2, hours=11),
                "unit_price": 950, "capacity": 30,
            },
        ]
        for row in rows:
            capacity = row["capacity"]
            lookup = {"service_type": row["service_type"], "provider_name": row["provider_name"], "title": row["title"]}
            defaults = {**row, "available_units": capacity, "currency": "NPR", "is_active": True}
            for key in lookup:
                defaults.pop(key, None)
            TravelOffering.objects.update_or_create(defaults=defaults, **lookup)
        self.stdout.write(self.style.SUCCESS(f"Demo travel inventory: {len(rows)} offerings"))

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

        # The named demo tourist owns the first few bookings, so signing in as
        # the documented account shows a populated "My Bookings" instead of an
        # empty list. The demo guide is assigned to them so the booking has
        # someone to message — chat rooms are keyed on the booking.
        featured = User.objects.filter(email="tourist@guideu.local").first()
        demo_guide = User.objects.filter(email="guide@guideu.local", role=User.Roles.GUIDE).first()

        created = 0
        for i in range(10):
            tourist, _ = User.objects.get_or_create(
                username=f"demo_tourist_{i}",
                defaults={
                    "email": f"demo_tourist_{i}@example.com",
                    "role": User.Roles.TOURIST,
                    "first_name": "Demo",
                    "last_name": f"Tourist {i}",
                },
            )
            # get_or_create never hashes a password, so these users used to be
            # created with an EMPTY password hash: they existed, they owned
            # bookings, and no one could ever log in as them. Reset it on every
            # run rather than only on creation — re-seeding before a demo should
            # restore known credentials, not preserve whatever is there.
            tourist.set_password(DEMO_PASSWORD)
            tourist.save(update_fields=["password"])
            if featured is not None and i < 3:
                tourist = featured

            route = routes[i % len(routes)]
            start = dt.date.today() + dt.timedelta(days=14 + i)
            end = start + dt.timedelta(days=route.duration_days)
            booking, _ = BookingSession.objects.get_or_create(
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
            # Repair on re-run: an earlier seed created these before the named
            # accounts existed, so ownership and the guide need updating.
            changes = {}
            if booking.tourist_id != tourist.pk:
                changes["tourist"] = tourist
            if demo_guide is not None and booking.assigned_guide_id != demo_guide.pk:
                changes["assigned_guide"] = demo_guide
            if changes:
                for field, value in changes.items():
                    setattr(booking, field, value)
                booking.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Demo bookings: {created}"))
        self._seed_demo_chat(featured, demo_guide)
        self._seed_demo_guide_requests(featured)

    def _seed_demo_guide_requests(self, tourist) -> None:
        if tourist is None:
            return
        from django.utils import timezone
        from src.bookings.models import GuideRequest

        rows = [
            ("GR-DEMO-001", "Thamel, Kathmandu", "Swayambhunath", 4, 2500),
            ("GR-DEMO-002", "Lakeside, Pokhara", "Sarangkot", 6, 3800),
        ]
        for reference, pickup, destination, hours, fare in rows:
            GuideRequest.objects.get_or_create(
                reference=reference,
                defaults={
                    "tourist": tourist, "pickup_name": pickup,
                    "destination_name": destination,
                    "scheduled_at": timezone.now() + dt.timedelta(days=2),
                    "duration_hours": hours, "group_size": 2,
                    "requirements": "English-speaking guide; first visit to the area.",
                    "proposed_fare": fare, "recommended_fare": fare,
                    "status": GuideRequest.Status.SEARCHING,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Demo guide requests: {len(rows)}"))

    def _seed_demo_chat(self, tourist, guide) -> None:
        """Give the featured booking an opening exchange to show in live chat.

        The chat screen is reached from a booking, and an empty thread looks
        identical to a broken socket. Two seeded messages make the difference
        visible before anything is typed.
        """
        if tourist is None or guide is None:
            return

        from src.bookings.models import BookingSession
        from src.chat.models import ChatMessage, ChatThread

        booking = BookingSession.objects.filter(tourist=tourist).order_by("pk").first()
        if booking is None:
            return

        thread, _ = ChatThread.objects.get_or_create(room=f"booking:{booking.pk}")
        thread.participants.add(tourist, guide)
        if thread.messages.exists():
            return

        opening = [
            (guide, "Namaste! I am Pemba, your guide for this trek. Do you have your permits sorted?"),
            (tourist, "Not yet - is the TIMS card something I arrange, or do you?"),
            (guide, "I arrange it. Bring two passport photos and we will do it in Kathmandu."),
        ]
        for sender, body in opening:
            ChatMessage.objects.create(thread=thread, sender=sender, body=body)
        self.stdout.write(self.style.SUCCESS(f"Demo chat: {len(opening)} messages on {thread.room}"))

    def _seed_demo_scam_reports(self, path: Path, region_cache: dict[str, "Region"], limit: int = 40) -> None:
        """Import a small slice of scam_reports.csv into the moderation queue.

        The full table stays out of the core DB on purpose — it is ML training
        data, not app state. But an empty /scam-reports page cannot demonstrate
        the trust-and-safety workflow at all, so this materialises a spread of
        severities that are still awaiting a decision, which is the only state
        in which the verify/dismiss actions are enabled.
        """
        from django.contrib.auth import get_user_model

        from src.trust.models import ScamReport, classify_severity

        if not path.exists():
            self.stdout.write(self.style.WARNING(f"{path.name} not found; skipping demo scam reports"))
            return

        User = get_user_model()
        reporter, _ = User.objects.get_or_create(
            username="demo_reporter",
            defaults={"email": "demo_reporter@example.com", "role": User.Roles.TOURIST},
        )
        reporter.set_password(DEMO_PASSWORD)
        reporter.save(update_fields=["password"])

        # Spread the slice across severity bands rather than taking the first N
        # rows, which are overwhelmingly "Fair" and would show a queue with
        # nothing worth acting on.
        per_band = max(1, limit // 5)
        buckets: dict[str, list[dict]] = {}
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                band = row.get("scam_severity", "")
                bucket = buckets.setdefault(band, [])
                if len(bucket) < per_band and row.get("region") in region_cache:
                    bucket.append(row)
                if all(len(b) >= per_band for b in buckets.values()) and len(buckets) >= 5:
                    break

        created = 0
        for row in (r for bucket in buckets.values() for r in bucket):
            ratio = float(row["overcharge_ratio"])
            _, made = ScamReport.objects.get_or_create(
                description=f"Imported from dataset row {row['report_id']}.",
                defaults={
                    "reporter": reporter,
                    "service_type": row["service_type"],
                    "region": region_cache[row["region"]],
                    "quoted_price_npr": int(row["quoted_price_npr"]),
                    "benchmark_price_npr": int(row["benchmark_price_npr"]),
                    "overcharge_ratio": ratio,
                    "scam_severity": classify_severity(ratio),
                    "was_flagged_by_app": row.get("was_flagged_by_app") == "True",
                    # Left SUBMITTED so the moderation actions are live in a demo.
                    "status": ScamReport.Status.SUBMITTED,
                },
            )
            created += int(made)
        self.stdout.write(self.style.SUCCESS(f"Demo scam reports: {created}"))

    # ---- helpers -----------------------------------------------------------
    def _bulk(self, model, objects: Iterator, label: str) -> None:
        total = 0
        with transaction.atomic():
            for batch in _chunked(objects, self.batch_size):
                model.objects.bulk_create(batch, batch_size=self.batch_size, ignore_conflicts=True)
                total += len(batch)
        self.stdout.write(self.style.SUCCESS(f"{label}: {total} rows processed"))
