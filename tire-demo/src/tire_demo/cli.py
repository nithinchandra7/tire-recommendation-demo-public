"""Developer commands and deterministic evidence exports."""

import csv
import hashlib
import io
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from .data import DATA_VERSION, records
from .engine import Engine
from .models import Filters, RecommendationRequest, Scenario
from .repository import SqliteRepository, snowflake_sql
from .settings import ROOT, Settings

OUTPUT = ROOT / "dist/tire-demo/artifacts"


def implementation_fingerprint() -> str:
    paths = sorted((ROOT / "tire-demo/src/tire_demo").glob("*.py"))
    paths = [p for p in paths if p.name not in {"cli.py", "media.py", "__init__.py"}]
    paths += sorted((ROOT / "tire-demo/sql/sqlite").glob("*.sql"))
    digest = hashlib.sha256()
    for file in paths:
        digest.update(str(file.relative_to(ROOT)).encode())
        digest.update(file.read_text().encode())
    return digest.hexdigest()


def scenarios() -> list[tuple[str, RecommendationRequest]]:
    names: list[Scenario] = ["standard", "nearby", "quantity", "stale", "no_match", "upgrade"]
    return [
        (
            s,
            RecommendationRequest(
                scenario=s, filters=Filters(budget=60 if s == "no_match" else 150)
            ),
        )
        for s in names
    ]


def evaluation() -> dict[str, Any]:
    (ROOT / "runtime").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "runtime") as temp:
        settings = replace(Settings(), database=Path(temp) / "evaluation.sqlite")
        repository = SqliteRepository(settings)
        engine = Engine(settings, repository, repository)
        results = []
        for name, request in scenarios():
            samples = [engine.recommend(request, "north") for _ in range(20)]
            sample = samples[-1]
            options = sample["recommendations"]
            passed = not options if name == "no_match" else bool(options)
            if name in {"nearby", "quantity", "stale"}:
                passed = passed and all(p["store_id"] != "S01" for p in options)
            if name == "upgrade":
                passed = passed and bool(sample["premium_option"])
            timings = sorted(s["trace"]["total_ms"] for s in samples)
            results.append(
                {
                    "scenario": name,
                    "passed": passed,
                    "runs": 20,
                    "p50_ms": round(statistics.median(timings), 3),
                    "p95_ms": round(timings[18], 3),
                    "output": sample,
                }
            )
        return {
            "implementation_fingerprint": implementation_fingerprint(),
            "dataset": DATA_VERSION,
            "products": 400,
            "locations": 8,
            "inventory_records": 3200,
            "environment": {
                "python": sys.version.split()[0],
                "backend": "SQLite",
                "provider": "fact templates",
                "clock": settings.clock,
            },
            "method": "20 sequential runs per scenario including persistence; p95 is nearest-rank.",
            "limits": (
                "Local synthetic workload only. Snowflake, Azure, cloud models and"
                " production outcomes are not measured."
            ),
            "scenarios": results,
            "passed": all(s["passed"] for s in results),
        }


def secrets_check() -> None:
    rules = [
        re.compile(r"-----BEGIN (?:RSA |EC |ENCRYPTED )?PRIVATE KEY-----"),
        re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
        re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    ]
    roots = [
        ROOT / "tire-demo",
        ROOT / "solution-labs",
        ROOT / "dist",
        ROOT / "scripts",
        ROOT / ".github",
    ]
    failures = []
    for directory in roots:
        for file in directory.rglob("*"):
            if not file.is_file() or file.suffix.lower() in {".zip", ".png", ".mp4", ".pyc"}:
                continue
            if "__pycache__" in file.parts:
                continue
            content = file.read_text(errors="ignore")
            if any(rule.search(content) for rule in rules):
                failures.append(str(file.relative_to(ROOT)))
    if failures:
        raise RuntimeError("Potential secret material in: " + ", ".join(failures))
    print("Secret-pattern checks passed (supplement with provider-aware scanning in CI).")


def structural_check() -> None:
    from xml.etree import ElementTree

    for file in OUTPUT.glob("*.svg"):
        ElementTree.parse(file)  # noqa: S314 - generated local SVG, no external input
    mandatory = [
        "README.md",
        "architecture.md",
        "evaluation.json",
        "evaluation.md",
        "openapi.json",
        "local-architecture.svg",
        "cloud-architecture.svg",
        "runtime-sequence.svg",
        "data-model.svg",
        "ingestion-flow.svg",
        "walkthrough.mp4",
        "walkthrough.vtt",
        "walkthrough-poster.png",
        "walkthrough-script.md",
        "review.md",
    ]
    missing = [name for name in mandatory if not (OUTPUT / name).is_file()]
    if missing:
        raise RuntimeError("Missing evidence artifacts: " + ", ".join(missing))
    expected_hashes = json.loads((OUTPUT / "manifest.json").read_text())["sha256"]
    actual_hashes = {
        file.name: hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(OUTPUT.iterdir())
        if file.is_file() and file.name not in {"manifest.json", "source.zip"}
    }
    if expected_hashes != actual_hashes:
        raise RuntimeError("Evidence manifest is stale; regenerate with make package")
    data = json.loads((OUTPUT / "evaluation.json").read_text())
    if not data["passed"]:
        raise RuntimeError("Scenario evaluation failed")
    if data.get("implementation_fingerprint") != implementation_fingerprint():
        raise RuntimeError("Implementation changed; regenerate evidence with make artifacts")
    from .app import create_app

    if json.loads((OUTPUT / "openapi.json").read_text()) != create_app(Settings()).openapi():
        raise RuntimeError("OpenAPI changed; regenerate evidence with make artifacts")
    html = (ROOT / "dist/tire-demo/index.html").read_text()
    for link in re.findall(r'(?:href|src)="(artifacts/[^"?#]+)', html):
        if not (ROOT / "dist/tire-demo" / link).is_file():
            raise RuntimeError("Broken artifact link: " + link)
    print("Artifact, SVG, evaluation and evidence-link checks passed.")


def export_artifacts() -> None:
    from .app import create_app

    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = evaluation()
    (OUTPUT / "evaluation.json").write_text(json.dumps(data, indent=2))
    lines = [
        "# Local scenario evaluation",
        "",
        f"Dataset: {DATA_VERSION}.",
        "",
        data["method"],
        "",
        "400 products; 8 locations; 3,200 inventory observations. SQLite + factual templates.",
        "",
        "| Scenario | Checks | p50 ms | p95 ms |",
        "|---|---|---:|---:|",
    ]
    lines.extend(
        f"| {s['scenario']} | {'PASS' if s['passed'] else 'FAIL'} | {s['p50_ms']} | {s['p95_ms']} |"
        for s in data["scenarios"]
    )
    lines.extend(
        [
            "",
            "## Measurement limits",
            "",
            data["limits"],
            "",
            (
                "Latency includes query, lookups, explanation and state "
                "persistence. No production SLA is claimed."
            ),
            "",
            (
                "A passing scenario check is not an independent verification of "
                "the original client engagement."
            ),
        ]
    )
    (OUTPUT / "evaluation.md").write_text("\n".join(lines) + "\n")
    (OUTPUT / "openapi.json").write_text(json.dumps(create_app(Settings()).openapi(), indent=2))
    for file in (ROOT / "tire-demo/docs").glob("*.md"):
        shutil.copyfile(file, OUTPUT / file.name)
    for table, rows in records(Settings().now()).items():
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path = ROOT / "tire-demo/data" / f"{table}.csv"
        path.parent.mkdir(exist_ok=True)
        path.write_text(buffer.getvalue())
    source = (ROOT / "tire-demo/sql/sqlite/recommend.sql").read_text()
    (ROOT / "tire-demo/sql/snowflake/recommend.sql").write_text(snowflake_sql(source))
    print("Exported real scenario outputs, timings, OpenAPI, documentation and synthetic CSVs.")


def package_source() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for file in (ROOT / "tire-demo/docs").glob("*.md"):
        shutil.copyfile(file, OUTPUT / file.name)
    hashes = {
        file.name: hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(OUTPUT.iterdir())
        if file.is_file() and file.name not in {"manifest.json", "source.zip"}
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(
            {"sha256": hashes, "scope": "Independent synthetic demonstration artifacts"}, indent=2
        )
        + "\n"
    )
    include = [
        "tire-demo/src",
        "tire-demo/tests",
        "tire-demo/tests-js",
        "tire-demo/sql",
        "tire-demo/data",
        "tire-demo/docs",
        "solution-labs",
        "dist",
        "scripts",
        ".github",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "requirements.lock",
        "requirements-dev.lock",
        "requirements-cloud.lock",
        "requirements-media.lock",
        "Makefile",
        "Dockerfile",
        ".dockerignore",
        ".gitignore",
        ".env.example",
        ".pre-commit-config.yaml",
        "eslint.config.mjs",
        "README.md",
        "CONTRIBUTING.md",
        "build-diagrams.cjs",
        "check-architectures.cjs",
        "ARCHITECTURE_REVIEW.md",
        "TECHNICAL_DEEP_DIVE_PLAN.md",
        "OTHER_PROJECTS_ARTIFACT_PLAN.md",
    ]
    with zipfile.ZipFile(OUTPUT / "source.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in include:
            path = ROOT / item
            files = path.rglob("*") if path.is_dir() else [path]
            for file in files:
                if (
                    not file.is_file()
                    or "__pycache__" in file.parts
                    or file.suffix in {".pyc", ".p8", ".pem", ".key"}
                    or file.name == "source.zip"
                ):
                    continue
                archive.write(file, str(file.relative_to(ROOT)))
    print("Packaged demo source and evidence (credentials and runtime state excluded).")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    if command == "seed":
        SqliteRepository(Settings.from_env())
        print("Synthetic catalog ready.")
    elif command == "artifacts":
        export_artifacts()
    elif command == "package":
        package_source()
    elif command == "check":
        structural_check()
    elif command == "secrets":
        secrets_check()
    elif command == "quick-check":
        secrets_check()
        for args in [
            [".venv/bin/ruff", "check", "tire-demo", "solution-labs", "scripts/native-smoke.py"],
            [
                ".venv/bin/ruff",
                "format",
                "--check",
                "tire-demo",
                "solution-labs",
                "scripts/native-smoke.py",
            ],
            ["npm", "run", "lint"],
            ["npm", "run", "format:check"],
        ]:
            subprocess.run(args, cwd=ROOT, check=True)  # noqa: S603 - fixed developer commands
    else:
        print("Commands: seed, artifacts, package, check, secrets, quick-check")


if __name__ == "__main__":
    main()
