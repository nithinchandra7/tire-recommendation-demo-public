"""Models select allowed emphasis keys; numerical and product claims come from facts."""

import json
from typing import Any
from urllib.parse import urlparse

import httpx

from .models import HighlightPlan
from .repository import Repository, SnowflakeRepository
from .settings import Settings, required_env


def select_highlights(settings: Settings, evidence: list[dict[str, Any]]) -> HighlightPlan:
    prompt = (
        'Return JSON only: {"highlights":["availability","comfort"]}. '
        "Choose 1-3 emphasis keys from availability, lead_time, wet_grip, comfort, budget. "
        "The application will render verified facts. Do not return text, "
        "numbers, SQL or product IDs. " + json.dumps(evidence, separators=(",", ":"))
    )
    if settings.provider == "cortex":
        rows = SnowflakeRepository().query(
            "SELECT AI_COMPLETE(:model,:prompt) AS response",
            {"model": required_env("CORTEX_MODEL"), "prompt": prompt},
        )
        raw = rows[0]["response"]
    elif settings.provider == "foundry":
        endpoint = required_env("AZURE_OPENAI_ENDPOINT").rstrip("/")
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".openai.azure.com"):
            raise ValueError("Use an HTTPS Azure OpenAI resource endpoint")
        with httpx.Client(timeout=8) as client:
            result = client.post(
                endpoint + "/openai/v1/chat/completions",
                headers={"api-key": required_env("AZURE_OPENAI_API_KEY")},
                json={
                    "model": required_env("AZURE_OPENAI_DEPLOYMENT"),
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            result.raise_for_status()
            raw = result.json()["choices"][0]["message"]["content"]
    else:
        return HighlightPlan(highlights=["availability", "comfort", "wet_grip"])
    return HighlightPlan.model_validate_json(raw if isinstance(raw, str) else json.dumps(raw))


def explain(
    settings: Settings, repository: Repository, candidates: list[dict[str, Any]], retailer: str
) -> dict[str, Any]:
    if not candidates:
        return {"mode": "template", "status": "no_candidates", "highlights": [], "context": []}
    params: dict[str, str | int | float] = {"retailer": retailer}
    for index, candidate in enumerate(candidates):
        params[f"p{index}"] = str(candidate["product_id"])
    placeholders = ",".join(f":p{i}" for i in range(len(candidates)))
    query = (  # noqa: S608 - only generated binding names; all values remain parameters
        "SELECT DISTINCT p.product_id,p.description FROM product p JOIN inventory i "  # noqa: S608 - generated binding names, parameterized values
        "ON p.product_id=i.product_id JOIN retailer_scope rs ON rs.store_id=i.store_id "
        f"WHERE rs.retailer_id=:retailer AND p.product_id IN ({placeholders})"
    )
    context = repository.query(query, params)
    status = "ready"
    try:
        highlights = select_highlights(
            settings,
            [
                {"product_id": c["product_id"], "comfort": c["comfort"], "wet_grip": c["wet_grip"]}
                for c in candidates
            ],
        ).highlights
        mode = settings.provider
    except Exception:
        highlights = ["availability", "comfort", "wet_grip"]
        mode, status = "template", "provider_fallback"
    for candidate in candidates:
        clauses = {
            "availability": (
                f"{candidate['available_quantity']} available at {candidate['location_name']}"
            ),
            "lead_time": f"Estimated lead time {candidate['lead_days']} day(s)",
            "wet_grip": f"Illustrative wet grip {candidate['wet_grip']}/10",
            "comfort": f"Illustrative comfort {candidate['comfort']}/10",
            "budget": f"Listed price ${candidate['price']:.2f} per tire",
        }
        candidate["explanation"] = ". ".join(clauses[key] for key in highlights) + "."
        candidate["highlight_keys"] = highlights
        candidate["citation"] = f"synthetic-catalog:{candidate['product_id']}"
    return {
        "mode": mode,
        "status": status,
        "highlights": highlights,
        "context": context,
        "policy": (
            "Models select emphasis keys; facts and citations are rendered by application code."
        ),
    }
