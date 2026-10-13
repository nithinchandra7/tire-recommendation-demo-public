"""SQL adapters and atomic local session/inventory operations."""

import importlib
import os
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Protocol

from .data import distance_miles, seed
from .models import Filters, InventoryUpdate
from .settings import Settings, identifier, required_env

Row = dict[str, Any]
Params = dict[str, str | int | float]


class StateConflictError(RuntimeError):
    """A newer owned session revision was committed during the request."""


def normalize_value(value: Any) -> Any:
    """Normalize connector FIXED values to the local numeric/JSON contract."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Nonfinite warehouse numeric value")
        return int(value) if value == value.to_integral_value() else float(value)
    return value


class Repository(Protocol):
    def query(self, sql: str, params: Params | None = None) -> list[Row]: ...


class SqliteRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        settings.database.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            seed(connection, settings.root, settings.now())

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.settings.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function("distance_miles", 4, distance_miles, deterministic=True)
        try:
            yield connection
        finally:
            connection.close()

    def query(self, sql: str, params: Params | None = None) -> list[Row]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(sql, params or {}).fetchall()]

    def load_state(self, session_id: str, retailer: str) -> tuple[Filters, int]:
        rows = self.query(
            "SELECT * FROM session_state WHERE session_id=:id AND retailer_id=:retailer",
            {"id": session_id, "retailer": retailer},
        )
        if not rows:
            raise LookupError("Session not found for this demo retailer")
        return Filters.model_validate_json(rows[0]["filters_json"]), int(rows[0]["revision"])

    def save_state(self, session_id: str, retailer: str, filters: Filters, revision: int) -> None:
        """Compare-and-swap using the revision read before recommendation computation."""
        with self.connection() as connection, connection:
            if revision == 0:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO session_state VALUES (?,?,?,?)",
                    (session_id, retailer, 1, filters.model_dump_json()),
                )
            else:
                cursor = connection.execute(
                    "UPDATE session_state SET revision=?,filters_json=? "
                    "WHERE session_id=? AND retailer_id=? AND revision=?",
                    (revision + 1, filters.model_dump_json(), session_id, retailer, revision),
                )
            if cursor.rowcount != 1:
                raise StateConflictError(
                    "Session changed during this request; retry the latest preferences"
                )

    def update_inventory(self, update: InventoryUpdate) -> str:
        payload = update.model_dump_json()
        with self.connection() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                "SELECT * FROM inventory_event WHERE event_id=?", (update.event_id,)
            ).fetchone()
            if prior:
                if prior["payload_json"] != payload:
                    raise ValueError("Event ID already exists with different content")
                return "duplicate"
            stock = connection.execute(
                "SELECT observed_epoch FROM inventory WHERE product_id=? AND store_id=?",
                (update.product_id, update.store_id),
            ).fetchone()
            if stock is None:
                raise LookupError("Inventory record not found")
            outcome = "applied" if update.observed_epoch > stock[0] else "older_ignored"
            if outcome == "applied":
                connection.execute(
                    (
                        "UPDATE inventory SET quantity=?,observed_epoch=? WHERE "
                        "product_id=? AND store_id=?"
                    ),
                    (update.quantity, update.observed_epoch, update.product_id, update.store_id),
                )
            connection.execute(
                "INSERT INTO inventory_event VALUES (?,?,?)", (update.event_id, payload, outcome)
            )
            return outcome


def snowflake_sql(sql: str) -> str:
    """Translate named value bindings; identifiers are fixed, separately validated."""
    return re.sub(r"(?<!:):([a-z_][a-z0-9_]*)", r"%(\1)s", sql)


class SnowflakeRepository:
    def __init__(self) -> None:
        self.config = {
            "account": required_env("SNOWFLAKE_ACCOUNT"),
            "user": required_env("SNOWFLAKE_USER"),
            "role": identifier(required_env("SNOWFLAKE_ROLE")),
            "warehouse": identifier(required_env("SNOWFLAKE_WAREHOUSE")),
            "database": identifier(required_env("SNOWFLAKE_DATABASE")),
            "schema": identifier(required_env("SNOWFLAKE_SCHEMA")),
            "private_key_file": required_env("SNOWFLAKE_PRIVATE_KEY_PATH"),
        }

    def query(self, sql: str, params: Params | None = None) -> list[Row]:
        try:
            connector = importlib.import_module("snowflake.connector")
        except ImportError as error:
            raise RuntimeError("Install the cloud extra before using Snowflake") from error
        config: dict[str, Any] = dict(self.config)
        passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        if passphrase:
            config["private_key_file_pwd"] = passphrase
        config.update(
            login_timeout=15,
            network_timeout=15,
            socket_timeout=15,
            session_parameters={
                "STATEMENT_TIMEOUT_IN_SECONDS": 10,
                "QUERY_TAG": "nithin_synthetic_tire_demo",
            },
        )
        with connector.connect(**config) as connection, connection.cursor() as cursor:
            cursor.execute(snowflake_sql(sql), params or {})
            if not cursor.description:
                return []
            keys = [str(column[0]).lower() for column in cursor.description]
            return [
                dict(zip(keys, (normalize_value(v) for v in row), strict=True))
                for row in cursor.fetchall()
            ]
