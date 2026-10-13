import importlib
import os
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest
from tire_demo.engine import Engine
from tire_demo.explanations import select_highlights
from tire_demo.models import HighlightPlan, RecommendationRequest
from tire_demo.repository import (
    SnowflakeRepository,
    SqliteRepository,
    normalize_value,
    snowflake_sql,
)
from tire_demo.settings import Settings, identifier


def test_placeholder_and_identifier_validation(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "YOUR_ACCOUNT")
    with pytest.raises(ValueError, match="SNOWFLAKE_ACCOUNT"):
        SnowflakeRepository()
    with pytest.raises(ValueError):
        identifier("DATABASE; DROP DATABASE")
    assert identifier("DEMO_SCHEMA_1") == "DEMO_SCHEMA_1"


def test_value_bindings_and_exported_sql(settings):
    local = (settings.root / "tire-demo/sql/sqlite/recommend.sql").read_text()
    assert (
        snowflake_sql(local)
        == (settings.root / "tire-demo/sql/snowflake/recommend.sql").read_text()
    )
    assert "%(retailer_id)s" in snowflake_sql(local)
    assert snowflake_sql("SELECT :value::VARCHAR") == "SELECT %(value)s::VARCHAR"


def test_decimal_normalization_and_nonfinite_rejection():
    assert normalize_value(Decimal("125.25")) == 125.25
    assert normalize_value(Decimal("8")) == 8
    with pytest.raises(ValueError):
        normalize_value(Decimal("NaN"))


def test_connector_lifecycle_parameters_and_decimal_results(monkeypatch):
    for name, value in {
        "ACCOUNT": "test-org-account",
        "USER": "test-user",
        "ROLE": "TEST_ROLE",
        "WAREHOUSE": "TEST_WH",
        "DATABASE": "TEST_DB",
        "SCHEMA": "TEST_SCHEMA",
        "PRIVATE_KEY_PATH": "./fictional-key.p8",
    }.items():
        monkeypatch.setenv("SNOWFLAKE_" + name, value)
    captured = {}

    class Cursor:
        description = [("PRICE",), ("QUANTITY",)]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            captured["cursor_closed"] = True

        def execute(self, sql, params):
            captured.update(sql=sql, params=params)

        def fetchall(self):
            return [(Decimal("125.25"), Decimal("8"))]

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            captured["connection_closed"] = True

        def cursor(self):
            return Cursor()

    def connect(**config):
        captured["config"] = config
        return Connection()

    original = importlib.import_module
    monkeypatch.setattr(
        importlib,
        "import_module",
        lambda name: (
            SimpleNamespace(connect=connect) if name == "snowflake.connector" else original(name)
        ),
    )
    rows = SnowflakeRepository().query("SELECT :value", {"value": "literal ' value"})
    assert rows == [{"price": 125.25, "quantity": 8}]
    assert (
        captured["sql"] == "SELECT %(value)s" and captured["params"]["value"] == "literal ' value"
    )
    assert captured["cursor_closed"] and captured["connection_closed"]
    assert captured["config"]["session_parameters"]["STATEMENT_TIMEOUT_IN_SECONDS"] == 10


def test_full_recommendation_with_mocked_snowflake_decimal_values(settings):
    local = SqliteRepository(settings)

    class DecimalRepository:
        def query(self, sql, params=None):
            rows = local.query(sql, params)
            # Normalize at the warehouse adapter boundary, as real connector rows do.
            return [
                {
                    key: normalize_value(Decimal(str(value))) if isinstance(value, float) else value
                    for key, value in row.items()
                }
                for row in rows
            ]

    result = Engine(settings, DecimalRepository(), local).recommend(
        RecommendationRequest(), "north"
    )
    assert result["recommendations"] and result["premium_option"]
    assert isinstance(result["recommendations"][0]["score"], float)


def test_optional_model_failure_preserves_recommendations(client, headers, monkeypatch):
    baseline = client.post("/api/tire/recommendations", headers=headers, json={}).json()

    def fail(*_args):
        raise Exception("connector-like provider failure")

    monkeypatch.setattr("tire_demo.explanations.select_highlights", fail)
    result = client.post("/api/tire/recommendations", headers=headers, json={}).json()
    assert [p["product_id"] for p in baseline["recommendations"]] == [
        p["product_id"] for p in result["recommendations"]
    ]
    assert result["explanation"]["status"] == "provider_fallback"


def test_model_keys_have_visible_effect_without_inventing_facts(client, headers, monkeypatch):
    monkeypatch.setattr(
        "tire_demo.explanations.select_highlights",
        lambda *_args: HighlightPlan(highlights=["budget", "wet_grip"]),
    )
    data = client.post("/api/tire/recommendations", headers=headers, json={}).json()
    product = data["recommendations"][0]
    assert product["explanation"].startswith(f"Listed price ${product['price']:.2f}")
    assert product["highlight_keys"] == ["budget", "wet_grip"]


def test_invalid_model_output_is_rejected():
    with pytest.raises(ValueError):
        HighlightPlan.model_validate({"highlights": ["invented_claim"]})
    with pytest.raises(ValueError):
        HighlightPlan.model_validate({"highlights": ["comfort"], "sql": "DROP TABLE inventory"})


def test_foundry_adapter_validates_and_uses_bounded_json(monkeypatch, settings):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test-resource.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fictional-key")
    calls = {}

    class Client:
        def __init__(self, **kwargs):
            calls.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def post(self, url, **kwargs):
            calls.update(url=url, **kwargs)
            return SimpleNamespace(
                raise_for_status=lambda: None,
                json=lambda: {"choices": [{"message": {"content": '{"highlights":["comfort"]}'}}]},
            )

    monkeypatch.setattr("tire_demo.explanations.httpx.Client", Client)
    plan = select_highlights(replace(settings, provider="foundry"), [])
    assert plan.highlights == ["comfort"] and calls["timeout"] == 8
    assert calls["url"].endswith("/openai/v1/chat/completions")
    assert calls["json"]["response_format"] == {"type": "json_object"}
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "http://example.com")
    with pytest.raises(ValueError, match="HTTPS"):
        select_highlights(replace(settings, provider="foundry"), [])


@pytest.mark.cloud
@pytest.mark.skipif(
    os.getenv("SNOWFLAKE_TEST_ENABLED") != "1",
    reason="Live Snowflake account not configured; opt-in connectivity check",
)
def test_live_snowflake_read_only_connectivity():
    assert SnowflakeRepository().query("SELECT 1 AS ok") == [{"ok": 1}]


def test_settings_reject_invalid_modes_and_naive_clock(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "unsupported")
    with pytest.raises(ValueError):
        Settings.from_env()
    with pytest.raises(ValueError):
        replace(Settings(), clock="2026-10-11T12:00:00").now()
