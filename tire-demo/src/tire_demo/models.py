"""Typed boundaries. Free-form text is never executed as SQL."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Scenario = Literal["standard", "nearby", "quantity", "stale", "no_match", "upgrade"]
Priority = Literal["balanced", "comfort", "wet", "budget"]


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: str | None = Field(default="V01", pattern=r"^V\d{2}$")
    size: str = Field(default="225/55R17", pattern=r"^\d{3}/\d{2}R\d{2}$")
    store_id: str = Field(default="S01", pattern=r"^S\d{2}$")
    quantity: int = Field(default=4, ge=1, le=8)
    budget: float = Field(default=150, ge=25, le=1000, allow_inf_nan=False)
    min_load_index: int = Field(default=98, ge=75, le=130)
    min_speed_rank: int = Field(default=4, ge=1, le=6)
    season: Literal["any", "all-season", "summer", "winter"] = "any"
    priority: Priority = "balanced"
    max_lead_days: int = Field(default=3, ge=0, le=14)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filters: Filters | None = None
    scenario: Scenario = "standard"
    session_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    follow_up: str = Field(default="", max_length=300)


class InventoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    product_id: str = Field(pattern=r"^T\d{4}$")
    store_id: str = Field(pattern=r"^S\d{2}$")
    quantity: int = Field(ge=0, le=10000)
    observed_epoch: int = Field(ge=0)


class HighlightPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    highlights: list[Literal["availability", "lead_time", "wet_grip", "comfort", "budget"]] = Field(
        min_length=1, max_length=3
    )


class Recommendation(BaseModel):
    product_id: str
    brand: str
    name: str
    tier: str
    size: str
    load_index: int
    speed_rank: int
    speed_symbol: str
    season: str
    price: float = Field(gt=0, allow_inf_nan=False)
    comfort: int = Field(ge=1, le=10)
    wet_grip: int = Field(ge=1, le=10)
    store_id: str
    location_name: str
    available_quantity: int = Field(ge=0)
    observed_epoch: int
    age_minutes: float = Field(ge=0, allow_inf_nan=False)
    distance: float = Field(ge=0, allow_inf_nan=False)
    lead_days: int = Field(ge=0)
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    score_contributions: dict[str, float]
    explanation: str
    citation: str
    highlight_keys: list[str]


class Upgrade(Recommendation):
    above_budget: bool
    extra_per_tire: float = Field(gt=0, allow_inf_nan=False)


class ExecutionStage(BaseModel):
    component: str
    label: str
    duration_ms: float = Field(ge=0, allow_inf_nan=False)


class ExecutionTrace(BaseModel):
    request_id: str
    stages: list[ExecutionStage]
    query_candidate_locations: int
    unique_recommendations: int
    retailer_scope: list[str]
    hard_constraints: list[str]
    filters: Filters
    preference_changes: list[str]
    weights: dict[str, float]
    data_version: str
    rules_version: str
    as_of: str
    scenario: Scenario
    simulation: str
    total_ms: float = Field(ge=0, allow_inf_nan=False)


class RecommendationResponse(BaseModel):
    session_id: str
    revision: int
    filters: Filters
    vehicle: dict[str, Any] | None
    recommendations: list[Recommendation]
    premium_option: Upgrade | None
    explanation: dict[str, Any]
    trace: ExecutionTrace
    no_result: dict[str, Any] | None
