#!/usr/bin/env python3
"""Run a real, black-box GuideU demo against the Docker stack.

The script intentionally uses only Python's standard library so a supervisor can
run it on a fresh machine after ``scripts/demo_setup_docker.sh``. It creates
unique demo accounts and exercises all three roles through the public HTTP
surfaces, including the actual Next.js administrator login form.
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from http.cookiejar import CookieJar
from typing import Any


CORE_API = os.getenv("GUIDEU_CORE_API", "http://localhost/api/v1").rstrip("/")
ADMIN_URL = os.getenv("GUIDEU_ADMIN_URL", "http://localhost:3000").rstrip("/")
GATEWAY_URL = os.getenv("GUIDEU_GATEWAY_URL", "http://localhost").rstrip("/")
ANALYTICS_URL = os.getenv("GUIDEU_ANALYTICS_URL", "http://localhost:8001").rstrip("/")
REALTIME_URL = os.getenv("GUIDEU_REALTIME_URL", "http://localhost:8002").rstrip("/")
ADMIN_EMAIL = os.getenv("GUIDEU_ADMIN_EMAIL", "admin@guideu.local")
ADMIN_PASSWORD = os.getenv("GUIDEU_ADMIN_PASSWORD", "AdminDemo123!")


class AcceptanceError(RuntimeError):
    pass


def report(label: str, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"[PASS] {label}{suffix}", flush=True)


def require(condition: bool, label: str, detail: str = "") -> None:
    if not condition:
        raise AcceptanceError(f"{label}: {detail or 'assertion failed'}")
    report(label, detail)


def json_request(
    path_or_url: str,
    *,
    method: str = "GET",
    token: str | None = None,
    payload: Any | None = None,
    expected: tuple[int, ...] = (200,),
    _attempt: int = 0,
) -> tuple[int, Any]:
    url = path_or_url if path_or_url.startswith("http") else f"{CORE_API}/{path_or_url.lstrip('/')}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status = response.status
            raw = response.read()
            retry_after = response.headers.get("Retry-After")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
        retry_after = exc.headers.get("Retry-After")
    except OSError as exc:
        raise AcceptanceError(f"Could not reach {url}: {exc}") from exc
    if status == 429 and status not in expected and _attempt < 3:
        delay = min(max(int(retry_after or "1"), 1), 60) + 1
        print(f"[WAIT] API throttle asked for {delay - 1}s; retrying safely", flush=True)
        time.sleep(delay)
        return json_request(
            path_or_url, method=method, token=token, payload=payload,
            expected=expected, _attempt=_attempt + 1,
        )
    try:
        data = json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        data = raw.decode("utf-8", errors="replace")
    if status not in expected:
        rendered = json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
        raise AcceptanceError(f"{method} {url} returned {status}, expected {expected}: {rendered[:900]}")
    return status, data


def items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]
    raise AcceptanceError(f"Expected a list or paginated response, received {type(data).__name__}")


def login(email: str, password: str) -> tuple[str, dict[str, Any]]:
    _, data = json_request("auth/token/", method="POST", payload={"email": email, "password": password})
    require(bool(data.get("access")), f"JWT login for {data.get('user', {}).get('role', 'account')}")
    return data["access"], data["user"]


def create_payment(token: str, target: dict[str, int], gateway: str, expected_amount: str) -> dict[str, Any]:
    malicious = {
        **target,
        "gateway": gateway,
        "amount": "1.00",
        "currency": "USD",
        "status": "REFUNDED",
        "mode": "live",
        "gateway_reference": "forged-reference",
    }
    _, payment = json_request("payments/payments/", method="POST", token=token, payload=malicious, expected=(201,))
    require(payment["amount"] == expected_amount, "Payment amount is computed by the server", payment["amount"])
    require(payment["currency"] == "NPR" and payment["status"] == "PENDING", "Payment lifecycle starts safely")
    require(payment["mode"] == "demo" and bool(payment["gateway_reference"]), "Local payment gateway demo initialized", gateway)
    _, confirmed = json_request(
        f"payments/payments/{payment['id']}/confirm/", method="POST", token=token, payload={}
    )
    require(confirmed["status"] == "SUCCESS", "Local payment confirmation succeeds", gateway)
    _, repeated = json_request(
        f"payments/payments/{payment['id']}/confirm/", method="POST", token=token, payload={}
    )
    require(repeated["status"] == "SUCCESS", "Payment confirmation is idempotent", gateway)
    return repeated


def multipart(fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----GuideUAcceptance{random.randrange(10**12):012d}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def exercise_admin_ui() -> None:
    cookies = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    try:
        with opener.open(f"{ADMIN_URL}/login", timeout=45) as response:
            html = response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        raise AcceptanceError(f"Could not load the administrator login page: {exc}") from exc
    action_match = re.search(r'name="(\$ACTION_ID_[^"]+)"', html)
    require(bool(action_match), "Next.js administrator login form renders")
    body, content_type = multipart(
        {action_match.group(1): "", "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    request = urllib.request.Request(
        f"{ADMIN_URL}/login",
        data=body,
        headers={"Content-Type": content_type, "Accept": "text/html"},
        method="POST",
    )
    try:
        with opener.open(request, timeout=60) as response:
            landing_url = response.geturl()
            landing = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise AcceptanceError(f"Administrator form login returned {exc.code}: {exc.read()[:500]!r}") from exc
    require("/dashboard" in landing_url and "GuideU Administration" not in landing, "Administrator form login keeps its HTTP session")

    pages = (
        "dashboard", "users", "guides", "bookings", "payments", "inventory",
        "reviews", "safety", "scam-reports", "models", "forecast", "festivals",
    )
    for page in pages:
        with opener.open(f"{ADMIN_URL}/{page}", timeout=60) as response:
            rendered = response.read().decode("utf-8", errors="replace")
            require(
                response.status == 200
                and "GuideU Administration" not in rendered
                and "Application error" not in rendered,
                f"Administrator /{page} page renders",
            )
    report("Administrator portal journey complete", f"{len(pages)} protected pages")


def main() -> int:
    suffix = f"{int(time.time())}{random.randrange(100, 999)}"
    tourist_email = f"acceptance.tourist.{suffix}@example.com"
    guide_email = f"acceptance.guide.{suffix}@example.com"
    password = "GuideUAcceptance123!"
    reset_password = "GuideUAcceptance456!"
    start = date.today() + timedelta(days=30)
    end = start + timedelta(days=3)
    scheduled = datetime.now(timezone.utc) + timedelta(hours=3)

    for label, url, expected_service in (
        ("Gateway core health", f"{GATEWAY_URL}/healthz", None),
        ("Gateway core health with slash", f"{GATEWAY_URL}/healthz/", None),
        ("Analytics model service", f"{ANALYTICS_URL}/health", "guideu-analytics-engine"),
        ("Realtime service", f"{REALTIME_URL}/health", "guideu-real-time-engine"),
    ):
        _, health = json_request(url)
        require(
            isinstance(health, dict)
            and health.get("status") == "healthy"
            and (expected_service is None or health.get("service") == expected_service),
            label,
        )
        if expected_service == "guideu-analytics-engine":
            require(
                health.get("models_loadable", 0) >= 5 and not health.get("unavailable"),
                "All trained ML artifacts load in the running container",
                str(health.get("models_loadable", 0)),
            )

    _, tourist = json_request(
        "auth/register/",
        method="POST",
        payload={
            "username": f"tourist_{suffix}", "email": tourist_email, "password": password,
            "first_name": "Acceptance", "last_name": "Tourist", "role": "TOURIST",
            "phone_number": "+9779800000001", "nationality": "Nepal",
        },
        expected=(201,),
    )
    _, guide = json_request(
        "auth/register/",
        method="POST",
        payload={
            "username": f"guide_{suffix}", "email": guide_email, "password": password,
            "first_name": "Acceptance", "last_name": "Guide", "role": "GUIDE",
            "phone_number": "+9779800000002", "nationality": "Nepal",
            "license_number": f"NTB-{suffix}", "bio": "Licensed multilingual mountain guide.",
            "service_areas": ["Kathmandu", "Everest/Khumbu"],
        },
        expected=(201,),
    )
    require(tourist["role"] == "TOURIST" and guide["role"] == "GUIDE", "Tourist and guide registration")

    tourist_token, _ = login(tourist_email, password)
    guide_token, _ = login(guide_email, password)
    admin_token, admin = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    require(admin["role"] == "ADMIN" and admin["is_staff"], "Administrator authorization")

    _, verified = json_request(
        f"auth/users/{guide['id']}/verify-guide/",
        method="POST", token=admin_token, payload={"verified": True},
    )
    require(verified["is_guide_verified"], "Administrator verifies guide")
    _, profile = json_request(
        "auth/users/guide-profile/",
        method="PATCH", token=guide_token,
        payload={
            "availability": "AVAILABLE", "current_latitude": "27.717245",
            "current_longitude": "85.323960", "hourly_rate_npr": "900.00",
            "daily_rate_npr": "6000.00",
        },
    )
    require(profile["availability"] == "AVAILABLE", "Guide publishes availability and location")
    _, preferences = json_request(
        "auth/users/preferences/", method="PATCH", token=tourist_token,
        payload={"language": "en", "currency": "NPR", "theme": "DARK", "safety_notifications": True},
    )
    require(preferences["theme"] == "DARK", "Tourist settings persist")

    _, routes = json_request(
        "recommendations/routes/?top_k=3&adventure=0.85&culture=0.65&nature=0.9",
        token=tourist_token,
    )
    require(routes["source"] == "ml" and len(routes["results"]) > 0, "ML route recommendations", routes.get("model_version", ""))
    _, guides = json_request(
        "recommendations/guides/?top_k=3&region=Everest%2FKhumbu&language=English",
        token=tourist_token,
    )
    require(guides["source"] == "ml" and len(guides["results"]) > 0, "ML guide recommendations", guides.get("model_version", ""))
    _, forecast = json_request(f"recommendations/forecast/?year={date.today().year + 1}", token=tourist_token)
    require(forecast["source"] == "ml" and len(forecast["items"]) == 12, "ML arrivals forecast", forecast.get("model_version", ""))
    _, price = json_request(
        "trust/price-check/", method="POST", token=tourist_token,
        payload={
            "service_type": "Licensed Guide", "region": "Everest/Khumbu",
            "season": "Peak", "quoted_price_npr": 25000,
        },
    )
    require(price["benchmark_price_npr"] is not None and price["source"], "Anti-scam fair-price check", price["source"])

    _, guide_request = json_request(
        "bookings/guide-requests/", method="POST", token=tourist_token,
        payload={
            "pickup_name": "Thamel", "pickup_latitude": "27.717245", "pickup_longitude": "85.323960",
            "destination_name": "Bhaktapur Durbar Square", "destination_latitude": "27.672200",
            "destination_longitude": "85.427800", "scheduled_at": scheduled.isoformat(),
            "duration_hours": 4, "group_size": 2, "requirements": "English-speaking heritage guide",
            "proposed_fare": "3500.00",
        },
        expected=(201,),
    )
    require(guide_request["status"] == "SEARCHING", "Tourist creates an on-demand guide request", guide_request["reference"])
    _, available_requests = json_request("bookings/guide-requests/", token=guide_token)
    require(any(row["id"] == guide_request["id"] for row in items(available_requests)), "Available guide sees the request")
    _, offer = json_request(
        f"bookings/guide-requests/{guide_request['id']}/offer/", method="POST", token=guide_token,
        payload={"offered_fare": "3600.00", "eta_minutes": 12, "message": "I can meet you in Thamel."},
        expected=(201,),
    )
    _, accepted = json_request(
        f"bookings/guide-requests/{guide_request['id']}/accept-offer/", method="POST", token=tourist_token,
        payload={"offer_id": offer["id"]},
    )
    require(accepted["accepted_guide"] == guide["id"] and accepted["status"] == "ACCEPTED", "Tourist accepts the guide offer")

    other_token, _ = login("demo_tourist_0@example.com", "TouristDemo123!")
    json_request(f"bookings/guide-requests/{guide_request['id']}/", token=other_token, expected=(404,))
    report("Guide request ownership isolation")
    room = f"guide-request:{guide_request['id']}"
    encoded_room = urllib.parse.quote(room, safe="")
    json_request(f"chat/threads/authorize/?room={encoded_room}", token=tourist_token)
    json_request(f"chat/threads/authorize/?room={encoded_room}", token=guide_token)
    json_request(f"chat/threads/authorize/?room={encoded_room}", token=other_token, expected=(403,))
    report("Chat room authorization isolates participants")
    _, first_message = json_request(
        "chat/messages/", method="POST", token=tourist_token,
        payload={"room": room, "body": "Namaste, I am near the main gate."}, expected=(201,),
    )
    json_request(
        "chat/messages/", method="POST", token=guide_token,
        payload={"room": room, "body": "Namaste, arriving in twelve minutes."}, expected=(201,),
    )
    _, history = json_request(f"chat/messages/?room={encoded_room}", token=tourist_token)
    require(any(message["id"] == first_message["id"] for message in history), "Durable tourist-guide chat history")

    guide_payment = create_payment(
        tourist_token, {"guide_request": guide_request["id"]}, "ESEWA", "3600.00"
    )
    for next_status in ("EN_ROUTE", "ARRIVED", "ACTIVE", "COMPLETED"):
        _, transitioned = json_request(
            f"bookings/guide-requests/{guide_request['id']}/transition/",
            method="POST", token=guide_token, payload={"status": next_status},
        )
        require(transitioned["status"] == next_status, f"Guide trip transitions to {next_status}")
    _, earnings = json_request("bookings/guide-requests/earnings/", token=guide_token)
    require(float(earnings["released_total"]) >= 3600 and earnings["released_trips"] >= 1, "Guide escrow is released into earnings")

    _, review = json_request(
        "reviews/reviews/", method="POST", token=tourist_token,
        payload={
            "guide_account": guide["id"], "rating": 5, "title": "Excellent local guide",
            "comment": "Clear communication, fair price, and a thoughtful heritage tour.",
        },
        expected=(201,),
    )
    require(review["status"] == "PENDING", "Tourist review enters moderation")
    _, moderated = json_request(
        f"reviews/reviews/{review['id']}/moderate/", method="POST", token=admin_token,
        payload={"status": "APPROVED"},
    )
    require(moderated["status"] == "APPROVED", "Administrator moderates the guide review")
    _, updated_earnings = json_request("bookings/guide-requests/earnings/", token=guide_token)
    require(updated_earnings["review_count"] >= 1 and float(updated_earnings["average_rating"]) == 5, "Guide portal shows rating and completed earnings")

    _, packages_data = json_request("bookings/packages/?page_size=1")
    package = items(packages_data)[0]
    _, package_booking = json_request(
        "bookings/bookings/", method="POST", token=tourist_token,
        payload={
            "tour_package": package["id"], "start_date": start.isoformat(),
            "end_date": end.isoformat(), "notes": "Acceptance demo package booking",
        },
        expected=(201,),
    )
    json_request(
        "bookings/itinerary-items/", method="POST", token=tourist_token,
        payload={
            "booking": package_booking["id"], "day_index": 1, "title": "Arrival briefing",
            "description": "Meet the guide and check equipment.",
        },
        expected=(201,),
    )
    package_payment = create_payment(
        tourist_token, {"booking": package_booking["id"]}, "KHALTI", package["base_price"]
    )
    _, package_confirmed = json_request(f"bookings/bookings/{package_booking['id']}/", token=tourist_token)
    require(package_confirmed["status"] == "CONFIRMED" and len(package_confirmed["itinerary_items"]) == 1, "Package booking and itinerary are confirmed")
    _, package_cancelled = json_request(
        f"bookings/bookings/{package_booking['id']}/cancel/", method="POST", token=tourist_token, payload={}
    )
    require(package_cancelled["status"] == "CANCELLED", "Tourist cancels package booking")
    _, refunded_package_payment = json_request(f"payments/payments/{package_payment['id']}/", token=tourist_token)
    require(refunded_package_payment["status"] == "REFUNDED", "Package cancellation refunds payment")

    for service_type in ("HOTEL", "FLIGHT", "BUS"):
        _, inventory = json_request(f"bookings/travel-offerings/?service_type={service_type}&page_size=10")
        require(len(items(inventory)) > 0, f"{service_type.title()} inventory is available")
    _, hotel_inventory = json_request("bookings/travel-offerings/?service_type=HOTEL&page_size=10")
    hotel = items(hotel_inventory)[0]
    stock_before = hotel["available_units"]
    hotel_end = start + timedelta(days=2)
    _, service_booking = json_request(
        "bookings/travel-service-bookings/", method="POST", token=tourist_token,
        payload={
            "offering": hotel["id"], "start_date": start.isoformat(), "end_date": hotel_end.isoformat(),
            "travellers": 2, "units": 1, "total_price": "1.00", "currency": "USD",
            "passenger_details": [{"name": "Acceptance Tourist"}],
            "special_requests": "Quiet room",
        },
        expected=(201,),
    )
    expected_hotel_total = f"{float(hotel['unit_price']) * 2:.2f}"
    require(service_booking["total_price"] == expected_hotel_total, "Hotel stay total is computed by nights")
    service_payment = create_payment(
        tourist_token, {"service_booking": service_booking["id"]}, "KHALTI", expected_hotel_total
    )
    _, service_confirmed = json_request(
        f"bookings/travel-service-bookings/{service_booking['id']}/", token=tourist_token
    )
    require(service_confirmed["status"] == "CONFIRMED", "Travel service booking is confirmed")
    _, service_cancelled = json_request(
        f"bookings/travel-service-bookings/{service_booking['id']}/cancel/",
        method="POST", token=tourist_token, payload={},
    )
    require(service_cancelled["status"] == "CANCELLED", "Travel booking cancellation")
    _, hotel_restored = json_request(f"bookings/travel-offerings/{hotel['id']}/")
    require(hotel_restored["available_units"] == stock_before, "Travel inventory is restored after cancellation")
    _, refunded_service_payment = json_request(f"payments/payments/{service_payment['id']}/", token=tourist_token)
    require(refunded_service_payment["status"] == "REFUNDED", "Travel cancellation refunds payment")

    _, workspace = json_request(
        "workspace/trips/", method="POST", token=tourist_token,
        payload={
            "title": "Nepal acceptance trip", "start_date": start.isoformat(), "end_date": end.isoformat(),
            "total_budget_npr": "75000.00", "currency_preference": "NPR",
            "notes": "Created by the live acceptance demo.",
        },
        expected=(201,),
    )
    _, workspace_item = json_request(
        "workspace/items/", method="POST", token=tourist_token,
        payload={
            "workspace": workspace["id"], "item_type": "custom", "custom_title": "Thamel food walk",
            "custom_description": "Try local Newari dishes.", "day_number": 1, "display_order": 0,
            "duration_minutes": 120, "estimated_cost_npr": "2500.00",
        },
        expected=(201,),
    )
    _, budget = json_request(f"workspace/trips/{workspace['id']}/budget-summary/", token=tourist_token)
    require(budget["total_planned_npr"] == 2500.0 and workspace_item["title"] == "Thamel food walk", "Trip workspace and live budget chart data")
    _, suggestions = json_request(f"workspace/trips/{workspace['id']}/ai-suggestions/", token=tourist_token)
    require(isinstance(suggestions["suggestions"], list), "AI trip-planning suggestions")

    _, scam_report = json_request(
        "trust/scam-reports/", method="POST", token=tourist_token,
        payload={
            "service_type": "Licensed Guide", "region": "Everest/Khumbu", "season": "Peak",
            "quoted_price_npr": 50000, "description": "The quoted amount was far above the in-app benchmark.",
        },
        expected=(201,),
    )
    _, verified_report = json_request(
        f"trust/scam-reports/{scam_report['id']}/verify/", method="POST", token=admin_token, payload={}
    )
    require(verified_report["status"] == "VERIFIED", "Scam report is calculated and admin-verified")

    _, sos = json_request(
        "safety/sos/", method="POST", token=tourist_token,
        payload={
            "latitude": "27.717245", "longitude": "85.323960",
            "message": "Acceptance test SOS; no real emergency.", "source": "APP",
        },
        expected=(201,),
    )
    _, active_sos = json_request("safety/sos/?status=ACTIVE", token=admin_token)
    require(any(row["id"] == sos["id"] for row in items(active_sos)), "Administrator receives tourist SOS")
    _, resolved_sos = json_request(
        f"safety/sos/{sos['id']}/resolve/", method="POST", token=admin_token, payload={}
    )
    require(resolved_sos["status"] == "RESOLVED" and resolved_sos["resolved_at"], "Administrator resolves SOS")

    _, unread = json_request("notifications/notifications/unread_count/", token=tourist_token)
    require(unread["unread"] > 0, "Tourist receives live workflow notifications", str(unread["unread"]))
    json_request("notifications/notifications/read_all/", method="POST", token=tourist_token, payload={})
    _, read = json_request("notifications/notifications/unread_count/", token=tourist_token)
    require(read["unread"] == 0, "Notification read-all setting")

    _, reset = json_request("auth/password-reset/", method="POST", payload={"email": tourist_email})
    require(bool(reset.get("debug_uid") and reset.get("debug_token")), "Local password reset issues a demo code")
    json_request(
        "auth/password-reset/confirm/", method="POST",
        payload={"uid": reset["debug_uid"], "token": reset["debug_token"], "new_password": reset_password},
    )
    login(tourist_email, reset_password)
    report("Password reset and re-login")

    for path, label in (
        ("auth/users/?page_size=5", "Admin user management API"),
        ("bookings/bookings/?page_size=5", "Admin booking management API"),
        ("payments/payments/?page_size=5", "Admin payment management API"),
        ("payments/escrow/?page_size=5", "Admin escrow ledger API"),
    ):
        _, admin_data = json_request(path, token=admin_token)
        require(isinstance(admin_data, (list, dict)), label)

    require(guide_payment["status"] == "SUCCESS", "Completed guide payment remains successful after escrow release")
    exercise_admin_ui()
    print("\nGuideU live acceptance demo completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AcceptanceError, AssertionError, KeyError, IndexError, TypeError, ValueError) as exc:
        print(f"\n[FAIL] {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
