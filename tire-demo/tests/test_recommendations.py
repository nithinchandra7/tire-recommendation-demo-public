import math

import pytest
from tire_demo.data import distance_miles, records
from tire_demo.engine import refine
from tire_demo.models import Filters
from tire_demo.repository import StateConflictError


def test_standard_result_enforces_business_requirements(client, headers, settings):
    response = client.post("/api/tire/recommendations", headers=headers, json={})
    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["status"] == "ready"
    assert len(data["recommendations"]) == 6
    assert len({p["product_id"] for p in data["recommendations"]}) == 6
    scores = [p["score"] for p in data["recommendations"]]
    assert scores == sorted(scores, reverse=True)
    for product in data["recommendations"]:
        assert product["size"] == "225/55R17"
        assert product["load_index"] >= 98 and product["speed_rank"] >= 4
        assert product["price"] <= 150 and product["available_quantity"] >= 4
        assert product["store_id"] in {"S01", "S02", "S03", "S04"}
        assert 0 <= product["age_minutes"] <= 30
        assert product["lead_days"] <= 3
        assert math.isclose(
            sum(product["score_contributions"].values()), product["score"], abs_tol=0.003
        )
        assert product["citation"].endswith(product["product_id"])
    assert data["trace"]["as_of"] == settings.now().isoformat()


@pytest.mark.parametrize("scenario", ["nearby", "quantity", "stale"])
def test_local_stock_failure_finds_scoped_alternatives(client, headers, scenario):
    data = client.post(
        "/api/tire/recommendations", headers=headers, json={"scenario": scenario}
    ).json()
    assert data["recommendations"]
    assert all(p["store_id"] != "S01" for p in data["recommendations"])


def test_no_results_does_not_relax_requirements(client, headers):
    data = client.post(
        "/api/tire/recommendations", headers=headers, json={"filters": {"budget": 60}}
    ).json()
    assert data["recommendations"] == []
    assert data["filters"]["budget"] == 60
    assert data["no_result"] and data["premium_option"] is None


def test_upgrade_is_separate_and_improves_attributes(client, headers):
    data = client.post("/api/tire/recommendations", headers=headers, json={}).json()
    upgrade = data["premium_option"]
    best = data["recommendations"][0]
    assert upgrade["above_budget"] and 150 < upgrade["price"] <= 187.5
    assert upgrade["comfort"] >= best["comfort"] and upgrade["wet_grip"] >= best["wet_grip"]
    assert upgrade["comfort"] > best["comfort"] or upgrade["wet_grip"] > best["wet_grip"]
    assert upgrade["available_quantity"] >= 4 and upgrade["age_minutes"] <= 30


def test_follow_up_preserves_session_and_merges_before_query(client, headers):
    first = client.post("/api/tire/recommendations", headers=headers, json={}).json()
    second = client.post(
        "/api/tire/recommendations",
        headers=headers,
        json={"session_id": first["session_id"], "follow_up": "quieter tires under $140"},
    ).json()
    assert second["session_id"] == first["session_id"] and second["revision"] == 2
    assert second["filters"]["priority"] == "comfort" and second["filters"]["budget"] == 140
    assert all(p["price"] <= 140 for p in second["recommendations"])
    assert second["trace"]["preference_changes"]
    state = next(s for s in second["trace"]["stages"] if s["component"] == "state")
    assert state["duration_ms"] >= 0


@pytest.mark.parametrize(
    "text",
    ["not winter tires", "no summer tires", "do not care about comfort, prioritize wet grip"],
)
def test_negated_preferences_require_clarification(text):
    with pytest.raises(ValueError, match="clarification"):
        refine(Filters(), text)


def test_unsupported_text_never_becomes_sql(client, headers):
    data = client.post(
        "/api/tire/recommendations",
        headers=headers,
        json={"follow_up": "SELECT * FROM product; DROP TABLE inventory"},
    ).json()
    assert data["recommendations"]
    assert data["filters"]["priority"] == "balanced"
    assert "No supported" in data["trace"]["preference_changes"][0]


def test_competing_preferences_require_clarification(client, headers):
    assert (
        client.post(
            "/api/tire/recommendations", headers=headers, json={"follow_up": "comfort and wet grip"}
        ).status_code
        == 422
    )


def test_openapi_exposes_typed_recommendation_response(client):
    schema = client.get("/api/openapi.json").json()
    response = schema["paths"]["/api/tire/recommendations"]["post"]["responses"]["200"]
    assert response["content"]["application/json"]["schema"]["$ref"].endswith(
        "RecommendationResponse"
    )


@pytest.mark.parametrize("filters", [{"store_id": "S05"}, {"store_id": "S99"}])
def test_store_scope_cannot_be_extended_by_request(client, headers, filters):
    assert (
        client.post(
            "/api/tire/recommendations", headers=headers, json={"filters": filters}
        ).status_code
        == 403
    )


def test_session_and_trace_are_owned(client, headers):
    data = client.post("/api/tire/recommendations", headers=headers, json={}).json()
    other = {"X-Demo-Retailer": "south"}
    assert (
        client.post(
            "/api/tire/recommendations", headers=other, json={"session_id": data["session_id"]}
        ).status_code
        == 404
    )
    trace = f"/api/tire/traces/{data['trace']['request_id']}"
    assert client.get(trace, headers=other).status_code == 404
    assert client.get(trace, headers=headers).status_code == 200


def test_simulated_identity_is_explicit_and_required(client):
    assert client.get("/api/health").json()["identity"] == "simulated"
    assert client.post("/api/tire/recommendations", json={}).status_code == 401


@pytest.mark.parametrize(
    "filters",
    [
        {"quantity": 0},
        {"budget": -1},
        {"size": "225' OR 1=1"},
        {"vehicle_id": "V99"},
        {"size": "205/55R16"},
        {"unrecognized": True},
    ],
)
def test_invalid_requests_and_conflicting_fitment(client, headers, filters):
    assert (
        client.post(
            "/api/tire/recommendations", headers=headers, json={"filters": filters}
        ).status_code
        == 422
    )


def test_vehicle_minimum_specs_cannot_be_lowered(client, headers):
    data = client.post(
        "/api/tire/recommendations",
        headers=headers,
        json={"filters": {"min_load_index": 75, "min_speed_rank": 1}},
    ).json()
    assert data["filters"]["min_load_index"] == 98 and data["filters"]["min_speed_rank"] == 4


def test_size_only_mode_and_south_network(client):
    data = client.post(
        "/api/tire/recommendations",
        headers={"X-Demo-Retailer": "south"},
        json={"filters": {"vehicle_id": None, "size": "205/55R16", "store_id": "S05"}},
    ).json()
    assert data["vehicle"] is None
    assert data["recommendations"]
    assert all(p["store_id"] in {"S05", "S06", "S07", "S08"} for p in data["recommendations"])


def test_compare_and_swap_rejects_late_state_write(client, headers):
    data = client.post("/api/tire/recommendations", headers=headers, json={}).json()
    store = client.app.state.store
    current, revision = store.load_state(data["session_id"], "north")
    newer = Filters.model_validate(current.model_dump() | {"priority": "wet"})
    store.save_state(data["session_id"], "north", newer, revision)
    with pytest.raises(StateConflictError):
        store.save_state(data["session_id"], "north", current, revision)
    stored, number = store.load_state(data["session_id"], "north")
    assert number == 2 and stored.priority == "wet"


def test_state_conflict_maps_to_409(client, headers, monkeypatch):
    def conflict(*_args):
        raise StateConflictError("Session changed")

    monkeypatch.setattr(client.app.state.store, "save_state", conflict)
    assert client.post("/api/tire/recommendations", headers=headers, json={}).status_code == 409


def test_dataset_is_reproducible_and_distance_is_geographic(settings):
    assert records(settings.now()) == records(settings.now())
    assert distance_miles(41.88, -87.63, 41.88, -87.63) == 0
    assert 5 < distance_miles(41.88, -87.63, 41.88, -87.75) < 7
