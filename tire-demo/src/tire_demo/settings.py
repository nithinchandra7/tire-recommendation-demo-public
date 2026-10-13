"""Explicit configuration. No cloud connection is made in local mode."""

import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(os.environ.get("TIRE_DEMO_ROOT", Path.cwd())).resolve()


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    backend: str = "sqlite"
    provider: str = "template"
    database: Path = ROOT / "runtime/tire-demo.sqlite"
    clock: str = "2026-10-11T12:00:00+00:00"
    max_age_minutes: int = 30

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(ROOT / ".env", override=False)
        backend = os.getenv("DATA_BACKEND", "sqlite")
        provider = os.getenv("AI_PROVIDER", "template")
        if backend not in {"sqlite", "snowflake"}:
            raise ValueError("DATA_BACKEND must be sqlite or snowflake")
        if provider not in {"template", "cortex", "foundry"}:
            raise ValueError("AI_PROVIDER must be template, cortex or foundry")
        age = int(os.getenv("INVENTORY_MAX_AGE_MINUTES", "30"))
        if not 1 <= age <= 120:
            raise ValueError("INVENTORY_MAX_AGE_MINUTES must be between 1 and 120")
        result = cls(
            backend=backend,
            provider=provider,
            database=ROOT / os.getenv("DEMO_DATABASE", "runtime/tire-demo.sqlite"),
            clock=os.getenv("DEMO_CLOCK", cls.clock),
            max_age_minutes=age,
        )
        result.now()
        return result

    def now(self) -> datetime:
        if self.backend == "snowflake":
            return datetime.now(UTC)
        value = datetime.fromisoformat(self.clock)
        if value.tzinfo is None:
            raise ValueError("DEMO_CLOCK must include a timezone")
        return value.astimezone(UTC)


def required_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value or "YOUR_" in value or value.startswith("/path/to/"):
        raise ValueError(f"Configure {name} before enabling this cloud provider")
    return value


def identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Snowflake identifiers must contain only letters, numbers and underscores")
    return name
