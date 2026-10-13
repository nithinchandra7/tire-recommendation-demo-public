from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tire_demo.app import create_app
from tire_demo.settings import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return replace(Settings(), database=tmp_path / "test.sqlite")


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as connection:
        yield connection


@pytest.fixture
def headers() -> dict[str, str]:
    return {"X-Demo-Retailer": "north"}
