from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    # "degraded" is a legitimate answer: the registry can list models whose
    # artifacts are not on this machine. What must hold is that the two agree.
    assert body["status"] in {"healthy", "degraded"}
    assert "models" in body
    assert (body["status"] == "healthy") == (body["unavailable"] == [])
    assert body["models_loadable"] == len(body["models"]) - len(body["unavailable"])


def test_scam_requires_api_key(client):
    resp = client.post("/api/v1/scam/score", json={"service_type": "Porter", "quoted_price_npr": 5000})
    assert resp.status_code == 401
