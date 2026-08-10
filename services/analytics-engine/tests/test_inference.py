from __future__ import annotations

import pytest


@pytest.mark.needs_dataset
def test_pricing_benchmark(client, api_headers):
    resp = client.post(
        "/api/v1/pricing/benchmark",
        headers=api_headers,
        json={"service_type": "Porter", "region": "Langtang"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["fair_price_npr"] > 0
    assert body["min_fair_npr"] <= body["fair_price_npr"] <= body["max_fair_npr"]


@pytest.mark.needs_dataset
def test_scam_score_flags_overcharge(client, api_headers):
    # First get a fair benchmark, then quote at 3x to force a flag.
    bench = client.post(
        "/api/v1/pricing/benchmark", headers=api_headers, json={"service_type": "Porter", "region": "Langtang"}
    ).json()
    quote = bench["fair_price_npr"] * 3
    resp = client.post(
        "/api/v1/scam/score",
        headers=api_headers,
        json={"service_type": "Porter", "region": "Langtang", "quoted_price_npr": quote},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_likely_scam"] is True
    assert body["overcharge_ratio"] > 1.25
    assert body["explanation"]
    assert body["below_fair_wage"] is False


@pytest.mark.needs_dataset
def test_scam_score_flags_below_fair_wage(client, api_headers):
    """A quote far *under* the fair floor for a labour service must be called out."""
    bench = client.post(
        "/api/v1/pricing/benchmark", headers=api_headers, json={"service_type": "Porter", "region": "Langtang"}
    ).json()
    resp = client.post(
        "/api/v1/scam/score",
        headers=api_headers,
        json={"service_type": "Porter", "region": "Langtang", "quoted_price_npr": bench["min_fair_npr"] * 0.5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["below_fair_range"] is True
    assert body["below_fair_wage"] is True
    assert "fair rate" in (body["fair_wage_message"] or "")


@pytest.mark.needs_dataset
def test_scam_score_ignores_fair_wage_for_non_labour(client, api_headers):
    """A cheap permit is a cheap permit, not an underpaid worker."""
    bench = client.post(
        "/api/v1/pricing/benchmark", headers=api_headers, json={"service_type": "TIMS Permit"}
    ).json()
    resp = client.post(
        "/api/v1/scam/score",
        headers=api_headers,
        json={"service_type": "TIMS Permit", "quoted_price_npr": bench["min_fair_npr"] * 0.5},
    )
    assert resp.status_code == 200
    assert resp.json()["below_fair_wage"] is False


@pytest.mark.needs_dataset
def test_recommend_routes(client, api_headers):
    resp = client.post(
        "/api/v1/recommendations/routes",
        headers=api_headers,
        json={"tourist": {"pref_adventure_score": 0.9, "budget_band": "Mid-range"}, "season": "Autumn", "top_k": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 5
    # High adventure score should surface harder routes near the top.
    assert body["items"][0]["components"]["adventure_match"] >= 0.5
    # Every recommendation carries its own explanation.
    assert all(item["why"] for item in body["items"])


@pytest.mark.needs_dataset
def test_recommendations_are_distinct_treks(client, api_headers):
    """The catalog stores each trek ~6 times; a top-k of duplicates is useless."""
    resp = client.post(
        "/api/v1/recommendations/routes",
        headers=api_headers,
        json={"tourist": {"pref_adventure_score": 0.7}, "top_k": 10},
    )
    names = [item["route_name"] for item in resp.json()["items"]]
    assert len(set(names)) == len(names)


@pytest.mark.needs_dataset
def test_recommendations_respond_to_the_profile(client, api_headers):
    """Two opposite profiles must not receive the same list."""
    def top_names(adventure: float) -> list[str]:
        resp = client.post(
            "/api/v1/recommendations/routes",
            headers=api_headers,
            json={"tourist": {"pref_adventure_score": adventure}, "top_k": 5},
        )
        return [item["route_name"] for item in resp.json()["items"]]

    assert top_names(0.05) != top_names(0.95)


def test_guide_rank(client, api_headers):
    resp = client.post(
        "/api/v1/guides/rank",
        headers=api_headers,
        json={
            "tourist": {"region": "Everest/Khumbu", "language": "English"},
            "candidates": [
                {"guide_id": "G1", "certification": "IFMGA Mountain Guide", "average_rating": 4.8, "regions_covered": "Everest/Khumbu", "languages_spoken": "Nepali, English"},
                {"guide_id": "G2", "certification": "City Guide (Licensed)", "average_rating": 3.5, "regions_covered": "Kathmandu Valley", "languages_spoken": "Nepali"},
            ],
        },
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["guide_id"] == "G1"  # IFMGA + region/language match ranks first


def test_guide_rank_demotes_expired_licence(client, api_headers):
    """An expired licence must not out-rank a current one on credentials alone."""
    resp = client.post(
        "/api/v1/guides/rank",
        headers=api_headers,
        json={
            "tourist": {"region": "Everest/Khumbu", "language": "English"},
            "candidates": [
                {"guide_id": "EXPIRED", "certification": "IFMGA Mountain Guide", "average_rating": 5.0,
                 "regions_covered": "Everest/Khumbu", "languages_spoken": "English", "verification_status": "Expired"},
                {"guide_id": "CURRENT", "certification": "NATHM Trekking Guide", "average_rating": 4.4,
                 "regions_covered": "Everest/Khumbu", "languages_spoken": "English", "verification_status": "Verified"},
            ],
        },
    )
    assert resp.json()["items"][0]["guide_id"] == "CURRENT"


@pytest.mark.needs_dataset
def test_segment_assignment(client, api_headers):
    resp = client.post(
        "/api/v1/segments/assign",
        headers=api_headers,
        json={"pref_adventure_score": 0.9, "pref_nature_score": 0.8, "price_sensitivity": 0.2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["segment_id"] is not None
    assert body["centroid"]


@pytest.mark.needs_dataset
def test_arrivals_forecast(client, api_headers):
    resp = client.post("/api/v1/forecast/arrivals", headers=api_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 12
    first = body["items"][0]
    assert first["lower_estimate"] <= first["predicted_arrivals"] <= first["upper_estimate"]
    # Autumn is Nepal's peak trekking season and the model should reproduce that.
    assert body["peak_month"] in (3, 4, 5, 9, 10, 11)
    # Default horizon is one year past the data, which the model can support.
    assert body["reliable"] is True
    assert body["year"] == body["last_observed_year"] + 1


@pytest.mark.needs_dataset
def test_forecast_flags_unreliable_horizon(client, api_headers):
    """Projecting years beyond the data must be labelled, not served as fact.

    The trend compounds a post-COVID recovery rate, so a request three years out
    returns a number far above anything the market could produce. It is still
    answered — but marked unreliable, with the reason in the note.
    """
    base = client.post("/api/v1/forecast/arrivals", headers=api_headers, json={}).json()
    far = client.post(
        "/api/v1/forecast/arrivals",
        headers=api_headers,
        json={"year": base["last_observed_year"] + 3},
    ).json()

    assert far["reliable"] is False
    assert far["horizon_years"] == 3
    assert "past the last observed year" in far["note"]
    # And the reason it is unreliable: the projection has run away from reality.
    assert sum(p["predicted_arrivals"] for p in far["items"]) > sum(
        p["predicted_arrivals"] for p in base["items"]
    )


def test_models_registry(client, api_headers):
    resp = client.get("/api/v1/models", headers=api_headers)
    assert resp.status_code == 200
    names = {card["name"] for card in resp.json()}
    assert {"scam_classifier", "route_recommender"} <= names
