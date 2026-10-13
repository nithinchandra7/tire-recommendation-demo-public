"""Repeatable fictional catalog and illustrative fitment; no client data."""

import math
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_VERSION = "synthetic-v1-seed-7"
RULES_VERSION = "eligibility-v1-ranking-v1"
SCOPES = {"north": ["S01", "S02", "S03", "S04"], "south": ["S05", "S06", "S07", "S08"]}


def distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 3958.8 * 2 * math.asin(math.sqrt(min(a, 1)))


def records(now: datetime) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(7)  # noqa: S311 - deterministic synthetic fixtures
    sizes = ["225/55R17", "235/60R18", "215/60R16", "245/45R19", "205/55R16"]
    brands = ["Trailform", "Ridgepoint", "Daymark", "Arcway"]
    products: list[dict[str, Any]] = []
    for index in range(400):
        tier = ["Essential", "Touring", "Premium"][index % 3]
        comfort, wet = rng.randint(5, 10), rng.randint(5, 10)
        product: dict[str, Any] = {
            "product_id": f"T{index + 1:04}",
            "brand": brands[index % 4],
            "name": f"{tier} {index + 1:03}",
            "size": sizes[index % 5],
            "load_index": rng.randint(98, 104),
            "speed_rank": rng.randint(3, 6),
            "speed_symbol": "",
            "season": ["all-season", "summer", "winter"][index % 3],
            "price": round(rng.uniform(90, 230), 2),
            "comfort": comfort,
            "wet_grip": wet,
            "warranty_miles": rng.choice([40000, 50000, 60000, 70000]),
            "tier": tier,
            "description": (
                f"Fictional {tier.lower()} tire. Illustrative comfort {comfort}/10 "
                f"and wet grip {wet}/10."
            ),
        }
        if index < 3:
            product.update(size="225/55R17", load_index=100, speed_rank=4, season="all-season")
            product.update(
                price=[125.0, 165.0, 140.0][index],
                comfort=[7, 10, 8][index],
                wet_grip=[7, 10, 8][index],
            )
            product["description"] = (
                "Illustrative product specification, not a manufacturer performance claim."
            )
        product["speed_symbol"] = ["S", "T", "H", "V", "W", "Y"][product["speed_rank"] - 1]
        products.append(product)
    locations: list[dict[str, Any]] = [
        {
            "store_id": f"S{i + 1:02}",
            "name": name,
            "kind": kind,
            "latitude": lat,
            "longitude": lon,
            "lead_days": days,
        }
        for i, (name, kind, lat, lon, days) in enumerate(
            [
                ("Loop retailer", "store", 41.882, -87.63, 0),
                ("West stockroom", "warehouse", 41.88, -87.72, 1),
                ("North retailer", "store", 41.99, -87.66, 0),
                ("Regional warehouse", "warehouse", 42.02, -87.9, 2),
                ("South retailer", "store", 41.75, -87.63, 0),
                ("South stockroom", "warehouse", 41.7, -87.7, 1),
                ("Lake retailer", "store", 41.72, -87.6, 0),
                ("South regional warehouse", "warehouse", 41.6, -87.85, 2),
            ]
        )
    ]
    vehicles = [
        {
            "vehicle_id": f"V{i + 1:02}",
            "name": name,
            "size": sizes[i],
            "min_load_index": 98,
            "min_speed_rank": 4,
            "fitment_version": "illustrative-fitment-v1",
        }
        for i, name in enumerate(
            [
                "Sample sedan",
                "Sample SUV",
                "Sample compact",
                "Sample sport sedan",
                "Sample hatchback",
            ]
        )
    ]
    inventory = [
        {
            "product_id": p["product_id"],
            "store_id": location["store_id"],
            "quantity": 8 if int(p["product_id"][1:]) <= 3 else rng.randint(0, 12),
            "observed_epoch": int(now.timestamp()) - rng.randint(4, 18) * 60,
        }
        for p in products
        for location in locations
    ]
    scopes = [{"retailer_id": r, "store_id": s} for r, stores in SCOPES.items() for s in stores]
    return {
        "product": products,
        "location": locations,
        "vehicle": vehicles,
        "inventory": inventory,
        "retailer_scope": scopes,
    }


def seed(connection: sqlite3.Connection, root: Path, now: datetime) -> None:
    connection.executescript((root / "tire-demo/sql/sqlite/schema.sql").read_text())
    if connection.execute("SELECT COUNT(*) FROM product").fetchone()[0]:
        return
    with connection:
        for table, rows in records(now).items():
            fields = list(rows[0])
            # Table and field identifiers originate only in this fixed generator.
            query = (
                f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})"  # noqa: S608
            )
            connection.executemany(query, [tuple(row[f] for f in fields) for row in rows])
