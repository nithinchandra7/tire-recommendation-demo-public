"""Scoped, explainable recommendations and preference transitions."""

import re
import secrets
from collections.abc import Callable
from time import perf_counter
from typing import Any

from .data import DATA_VERSION, RULES_VERSION
from .explanations import explain
from .models import Filters, RecommendationRequest
from .repository import Params, Repository, SqliteRepository
from .settings import Settings

WEIGHTS = {
    "balanced": (0.25, 0.25, 0.20, 0.15, 0.15),
    "comfort": (0.50, 0.15, 0.10, 0.10, 0.15),
    "wet": (0.15, 0.50, 0.10, 0.10, 0.15),
    "budget": (0.10, 0.10, 0.55, 0.10, 0.15),
}


def refine(filters: Filters, text: str) -> tuple[Filters, list[str]]:
    updates: dict[str, Any] = {}
    value = text.lower()
    if re.search(r"\b(?:not|no|without|avoid|don't|do not)\b", value):
        raise ValueError(
            "Negated preferences need clarification. Use positive preferences or the form."
        )
    priorities = {
        "comfort": any(word in value for word in ["quiet", "comfort", "smooth"]),
        "wet": any(word in value for word in ["wet", "rain", "grip"]),
        "budget": any(word in value for word in ["cheap", "lower price", "lower cost"]),
    }
    if sum(priorities.values()) > 1:
        raise ValueError("Choose one ranking priority, or select Balanced choice in the form.")
    if any(word in value for word in ["quiet", "comfort", "smooth"]):
        updates["priority"] = "comfort"
    elif any(word in value for word in ["wet", "rain", "grip"]):
        updates["priority"] = "wet"
    elif any(word in value for word in ["cheap", "cost", "budget"]):
        updates["priority"] = "budget"
    match = re.search(r"(?:under|below|budget(?: of)?|up to)\s*\$?\s*(\d+(?:\.\d+)?)", value)
    if match:
        updates["budget"] = float(match.group(1))
    for season in ["winter", "summer", "all-season"]:
        if season in value:
            updates["season"] = season
    updated = Filters.model_validate(filters.model_dump() | updates)
    changes = [
        f"{key}: {getattr(filters, key)} → {item}"
        for key, item in updates.items()
        if getattr(filters, key) != item
    ]
    if text and not updates:
        changes = [
            "No supported preference detected. Use the form to change size, quantity or delivery."
        ]
    return updated, changes


def deduplicate(rows: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["product_id"] not in selected:
            selected[row["product_id"]] = row
    return list(selected.values())[:limit]


class Engine:
    def __init__(self, settings: Settings, repository: Repository, state: SqliteRepository) -> None:
        self.settings, self.repository, self.state = settings, repository, state

    def recommend(self, request: RecommendationRequest, retailer: str) -> dict[str, Any]:
        started = perf_counter()
        stages: list[dict[str, Any]] = []

        def stage(component: str, label: str, call: Callable[[], Any]) -> Any:
            before = perf_counter()
            result = call()
            stages.append(
                {
                    "component": component,
                    "label": label,
                    "duration_ms": round((perf_counter() - before) * 1000, 3),
                }
            )
            return result

        scopes = stage(
            "api",
            "Resolve server-defined demo retailer scope",
            lambda: self.repository.query(
                "SELECT store_id FROM retailer_scope WHERE retailer_id=:retailer",
                {"retailer": retailer},
            ),
        )
        allowed = [row["store_id"] for row in scopes]
        session_id = request.session_id or secrets.token_hex(16)
        previous: Filters | None = None
        revision = 0
        if request.session_id:
            previous, revision = self.state.load_state(session_id, retailer)
        filters = request.filters or previous or Filters()
        filters, changes = stage(
            "state",
            "Merge typed preferences before querying",
            lambda: refine(filters, request.follow_up),
        )
        if filters.store_id not in allowed:
            raise PermissionError("Store is outside this demo retailer's assigned scope")
        vehicle = None
        if filters.vehicle_id:
            vehicles = self.repository.query(
                "SELECT * FROM vehicle WHERE vehicle_id=:id", {"id": filters.vehicle_id}
            )
            if not vehicles:
                raise ValueError("Unknown illustrative vehicle")
            vehicle = vehicles[0]
            if filters.size != vehicle["size"]:
                raise ValueError(
                    "Size differs from sample vehicle fitment. Select size-only mode "
                    "or its assigned size."
                )
            filters = Filters.model_validate(
                filters.model_dump()
                | {
                    "min_load_index": max(filters.min_load_index, vehicle["min_load_index"]),
                    "min_speed_rank": max(filters.min_speed_rank, vehicle["min_speed_rank"]),
                }
            )
        location = self.repository.query(
            "SELECT * FROM location WHERE store_id=:id", {"id": filters.store_id}
        )[0]
        weights = WEIGHTS[filters.priority]
        observation_time = self.settings.now()
        as_of = int(observation_time.timestamp())
        params: Params = {
            "retailer_id": retailer,
            "store_id": filters.store_id,
            "scenario": request.scenario,
            "size": filters.size,
            "min_load": filters.min_load_index,
            "min_speed": filters.min_speed_rank,
            "season": filters.season,
            "budget": filters.budget,
            "quantity": filters.quantity,
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "as_of": as_of,
            "fresh_after": as_of - self.settings.max_age_minutes * 60,
            "max_lead": filters.max_lead_days,
            **dict(
                zip(
                    ["w_comfort", "w_wet", "w_price", "w_distance", "w_delivery"],
                    weights,
                    strict=True,
                )
            ),
        }
        sql = (self.settings.root / "tire-demo/sql/sqlite/recommend.sql").read_text()
        rows = stage(
            "sql",
            "SQL eligibility, inventory joins and ranking (one measured query)",
            lambda: self.repository.query(sql, params),
        )
        candidates = deduplicate(rows)
        premium_rows = (
            self.repository.query(sql, params | {"budget": round(filters.budget * 1.25, 2)})
            if candidates
            else []
        )
        premium = None
        if candidates:
            best = candidates[0]
            for row in deduplicate(premium_rows, 400):
                if (
                    row["price"] > filters.budget
                    and row["comfort"] >= best["comfort"]
                    and row["wet_grip"] >= best["wet_grip"]
                    and (row["comfort"] > best["comfort"] or row["wet_grip"] > best["wet_grip"])
                ):
                    premium = row | {
                        "above_budget": True,
                        "extra_per_tire": round(row["price"] - best["price"], 2),
                    }
                    break
        for candidate in candidates + ([premium] if premium else []):
            candidate["distance"] = round(candidate["distance"], 1)
            candidate["age_minutes"] = round((as_of - candidate["observed_epoch"]) / 60, 1)
            candidate["score_contributions"] = {
                name: round(100 * weight * candidate[f"{feature}_feature"], 3)
                for name, feature, weight in zip(
                    ["Comfort", "Wet grip", "Price", "Proximity", "Delivery"],
                    ["comfort", "wet", "price", "proximity", "delivery"],
                    weights,
                    strict=True,
                )
            }
        evidence = candidates + ([premium] if premium else [])
        explanation = stage(
            "explain",
            "Scoped product facts and bounded explanations",
            lambda: explain(self.settings, self.repository, evidence, retailer),
        )
        self.state.save_state(session_id, retailer, filters, revision)
        trace = {
            "request_id": secrets.token_hex(8),
            "stages": stages,
            "query_candidate_locations": len(rows),
            "unique_recommendations": len(candidates),
            "retailer_scope": allowed,
            "hard_constraints": [
                "illustrative fitment",
                "minimum load/speed",
                "quantity at one location",
                "freshness",
                "delivery limit",
            ],
            "filters": filters.model_dump(),
            "preference_changes": changes,
            "weights": dict(
                zip(["Comfort", "Wet grip", "Price", "Proximity", "Delivery"], weights, strict=True)
            ),
            "data_version": DATA_VERSION,
            "rules_version": RULES_VERSION,
            "as_of": observation_time.isoformat(),
            "scenario": request.scenario,
            "simulation": "Scenario overrides are request-local; stored inventory is unchanged.",
            "total_ms": round((perf_counter() - started) * 1000, 3),
        }
        return {
            "session_id": session_id,
            "revision": revision + 1,
            "filters": filters.model_dump(),
            "vehicle": vehicle,
            "recommendations": candidates,
            "premium_option": premium,
            "explanation": explanation,
            "trace": trace,
            "no_result": None
            if candidates
            else {
                "message": "No product meets all current requirements.",
                "suggestions": [
                    "Increase budget explicitly",
                    "Allow a longer lead time",
                    "Choose another permitted store",
                ],
                "preserved": "Fitment, minimum specifications and freshness remain enforced.",
            },
        }
