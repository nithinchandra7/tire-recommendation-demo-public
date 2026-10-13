"""Render a captioned walkthrough from actual synthetic-engine outputs, not client screenshots."""

import importlib
import json
import textwrap
from dataclasses import replace
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .cli import OUTPUT
from .engine import Engine
from .models import RecommendationRequest
from .repository import SqliteRepository
from .settings import ROOT, Settings

PAPER = "#f6f5ef"
INK = "#192d26"
GREEN = "#1d4437"
MUTED = "#69716a"
LIME = "#dfea9d"
CHAPTERS = [
    (
        "Start with the customer.",
        "Four tires. A clear budget. Explicit requirements.",
        (
            "Four compatible tires, a $150 budget and a three-day lead time. "
            "All products, stock and fitment records are fictional."
        ),
    ),
    (
        "Good options. Clear reasons.",
        "Actual outputs from the standard synthetic scenario.",
        (
            "SQL enforces compatibility and fresh stock, then ranks eligible "
            "products. Product cards expose prices, locations and factor "
            "scores."
        ),
    ),
    (
        "Unavailable here? Look nearby.",
        "Search another permitted location without weakening fitment.",
        (
            "The selected store has no stock in this request. Compatible "
            "alternatives come from another location within the retailer's "
            "assigned scope."
        ),
    ),
    (
        "Refine the preference.",
        "Quieter tires under $140. Merge first, then query.",
        (
            "A follow-up changes the comfort priority and budget before "
            "querying. The session revision and resulting options record that "
            "transition."
        ),
    ),
    (
        "Stock has a clock.",
        "Exclude stale observations. Inspect the actual execution.",
        (
            "The local observation is two hours old and is excluded. Returned "
            "stock is fresh; query timing and score contributions are measured"
            " evidence."
        ),
    ),
    (
        "Inspect the architecture.",
        "Implemented locally. Cloud connections are configurable.",
        (
            "The local demo runs on FastAPI and SQLite. Snowflake and Azure "
            "need configuration. Explore the source, diagrams, decisions and "
            "evaluation."
        ),
    ),
]


def font(size: int, serif: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "/System/Library/Fonts/Supplemental/Georgia.ttf"
        if serif
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
        if serif
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in paths:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    size: int = 18,
    color: str = INK,
    width: int = 90,
) -> None:
    draw.multiline_text(
        xy, "\n".join(textwrap.wrap(value, width)), font=font(size), fill=color, spacing=8
    )


def scene(index: int, outputs: dict[str, Any], refined: dict[str, Any]) -> Image.Image:
    image = Image.new("RGB", (1280, 720), PAPER)
    draw = ImageDraw.Draw(image)
    text(draw, (45, 25), "nc.  Nithin Chandra", 22)
    text(draw, (880, 31), "TIRE LAB / INDEPENDENT DEMONSTRATION", 11, MUTED)
    draw.line((45, 70, 1235, 70), fill="#d6d9cf")
    text(draw, (45, 93), f"0{index + 1} / 06   SYNTHETIC DATA · ACTUAL DEMO OUTPUTS", 11, MUTED)
    text(draw, (45, 131), CHAPTERS[index][0], 43, width=60)
    text(draw, (45, 195), CHAPTERS[index][1], 19, MUTED)
    if index in {1, 2, 3, 4}:
        data = refined if index == 3 else outputs[{1: "standard", 2: "nearby", 4: "stale"}[index]]
        for column, product in enumerate(data["recommendations"][:3]):
            x = 45 + column * 400
            draw.rounded_rectangle(
                (x, 255, x + 375, 543), radius=8, fill="#fbfaf6", outline="#cbd4c0", width=2
            )
            text(
                draw,
                (x + 20, 273),
                f"OPTION {column + 1} · {product['score']:.1f} POINTS",
                11,
                MUTED,
            )
            text(draw, (x + 20, 308), f"{product['brand']} {product['name']}", 22, width=29)
            text(
                draw,
                (x + 20, 358),
                f"{product['size']} · {product['load_index']}{product['speed_symbol']}",
                15,
                MUTED,
            )
            text(draw, (x + 20, 393), f"${product['price']:.2f} / tire", 27)
            text(
                draw,
                (x + 20, 438),
                f"{product['available_quantity']} available · {product['location_name']}",
                15,
                width=35,
            )
            text(
                draw,
                (x + 20, 474),
                f"Lead: {product['lead_days']} day(s) · observed {product['age_minutes']} min ago",
                13,
                MUTED,
                width=42,
            )
            text(
                draw,
                (x + 20, 508),
                f"Comfort {product['comfort']}/10 · wet grip {product['wet_grip']}/10",
                13,
                MUTED,
            )
        query_time = next(
            s["duration_ms"] for s in data["trace"]["stages"] if s["component"] == "sql"
        )
        pair_count = data["trace"]["query_candidate_locations"]
        label = (
            f"State revision {refined['revision']} · comfort priority · $140 budget"
            if index == 3
            else f"SQL query: {query_time:.3f} ms · {pair_count} eligible product/location pairs"
        )
        text(draw, (45, 566), label, 16, GREEN)
        text(
            draw,
            (45, 598),
            (
                "Illustrative product ratings. Stock is an observation; "
                "reservation remains a separate operation."
            ),
            13,
            MUTED,
        )
    elif index == 0:
        requirements = [
            ("Sample sedan", "225/55R17 · minimum 98V"),
            ("Quantity / budget", "4 tires · $150 per tire"),
            ("Availability / preferences", "Fresh stock · 3 days · balanced"),
        ]
        for row, (title, value) in enumerate(requirements):
            y = 260 + row * 103
            draw.rounded_rectangle((45, y, 790, y + 81), radius=7, fill="#e9eddf")
            text(draw, (65, y + 13), title.upper(), 11, MUTED)
            text(draw, (65, y + 38), value, 23)
        draw.rounded_rectangle((825, 260, 1235, 547), radius=7, fill=GREEN)
        text(draw, (850, 286), "THE DECISION FLOW", 12, LIME)
        for row, label in enumerate(
            [
                "Typed requirements",
                "Scoped SQL eligibility",
                "Fresh stock + ranking",
                "Facts + alternatives",
            ]
        ):
            text(draw, (850, 331 + row * 49), f"0{row + 1}  {label}", 20, PAPER)
        text(
            draw,
            (45, 590),
            "400 fictional products · 8 sample locations · 3,200 inventory observations",
            16,
            MUTED,
        )
    else:
        layers = [
            ("Browser → Python API", "Requirements, scope and typed state"),
            ("SQLite → Snowflake adapter", "Parameter binding, eligibility and ranking"),
            ("Facts → optional model emphasis", "Templates work without cloud credentials"),
            ("Trace → evidence package", "Source, diagrams, decisions and real local evaluation"),
        ]
        for row, (title, value) in enumerate(layers):
            y = 255 + row * 79
            draw.rounded_rectangle((45, y, 1235, y + 64), radius=6, fill="#e9eddf")
            text(draw, (65, y + 14), title, 19)
            text(draw, (570, y + 19), value, 16, MUTED, width=64)
        text(
            draw,
            (45, 590),
            (
                "Cloud identity, ingestion and shared state are reference "
                "bindings. Original client outcomes are separate."
            ),
            15,
            MUTED,
            width=115,
        )
    draw.line((45, 640, 1235, 640), fill="#d6d9cf")
    text(
        draw,
        (45, 658),
        (
            "Rendered walkthrough of actual synthetic outputs · not a "
            "recording of the client application"
        ),
        12,
        MUTED,
    )
    return image


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evaluation = json.loads((OUTPUT / "evaluation.json").read_text())
    outputs = {item["scenario"]: item["output"] for item in evaluation["scenarios"]}
    settings = replace(Settings(), database=ROOT / "runtime/media.sqlite")
    repository = SqliteRepository(settings)
    engine = Engine(settings, repository, repository)
    first = engine.recommend(RecommendationRequest(), "north")
    refined = engine.recommend(
        RecommendationRequest(session_id=first["session_id"], follow_up="quieter tires under $140"),
        "north",
    )
    (OUTPUT / "walkthrough-refinement.json").write_text(json.dumps(refined, indent=2))
    scenes = [scene(i, outputs, refined) for i in range(6)]
    scenes[1].save(OUTPUT / "walkthrough-poster.png")
    cues = ["WEBVTT", ""]
    for index, chapter in enumerate(CHAPTERS):
        start = index * 20
        end = (index + 1) * 20
        cues.extend(
            [
                str(index + 1),
                f"00:{start // 60:02}:{start % 60:02}.000 --> 00:{end // 60:02}:{end % 60:02}.000",
                chapter[2],
                "",
            ]
        )
    (OUTPUT / "walkthrough.vtt").write_text("\n".join(cues))
    ffmpeg = importlib.import_module("imageio_ffmpeg")
    writer = ffmpeg.write_frames(
        str(OUTPUT / "walkthrough.mp4"),
        (1280, 720),
        fps=6,
        codec="libx264",
        quality=7,
        output_params=["-movflags", "+faststart"],
        macro_block_size=1,
    )
    writer.send(None)
    try:
        for frame in range(720):
            image = scenes[frame // 120].copy()
            draw = ImageDraw.Draw(image)
            draw.rectangle((45, 700, 1235, 705), fill="#d6d9cf")
            draw.rectangle((45, 700, 45 + int(1190 * (frame + 1) / 720), 705), fill="#80954b")
            writer.send(image.tobytes())
    finally:
        writer.close()
    print("Exported 120-second captioned walkthrough, poster and actual refinement evidence.")


if __name__ == "__main__":
    main()
