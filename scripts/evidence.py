"""Package and verify one independent project's source and executed evidence."""

import hashlib
import importlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "repository.json").read_text())
PROJECT = CONFIG["project"]
OUTPUT = ROOT / "dist" / f"{PROJECT}-demo" / "artifacts"
INCLUDE = [
    "PUBLIC_SCOPE.md",
    "src",
    "tests",
    "tests-js",
    "tire-demo",
    "solution-labs",
    "dist",
    "scripts",
    ".github",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "Makefile",
    ".gitignore",
    ".gitleaks.toml",
    ".env.example",
    ".pre-commit-config.yaml",
    "eslint.config.mjs",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "repository.json",
    "requirements.lock",
    "requirements-dev.lock",
    "requirements-cloud.lock",
    "requirements-media.lock",
]


def files() -> list[Path]:
    result = []
    for item in INCLUDE:
        path = ROOT / item
        for file in path.rglob("*") if path.is_dir() else [path]:
            if not file.is_file() or file.name == "source.zip":
                continue
            if "__pycache__" in file.parts or file.suffix in {".pyc", ".pem", ".p8", ".key"}:
                continue
            result.append(file)
    return sorted(result)


def schema() -> dict[str, Any]:
    return cast(
        dict[str, Any], importlib.import_module(CONFIG["app"].split(":")[0]).create_app().openapi()
    )


def hashes() -> dict[str, str]:
    return {
        file.name: hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(OUTPUT.iterdir())
        if file.is_file() and file.name not in {"source.zip", "manifest.json"}
    }


def package() -> None:
    docs = ROOT / CONFIG["docs"]
    for file in docs.glob("*.md"):
        shutil.copyfile(file, OUTPUT / file.name)
    (OUTPUT / "manifest.json").write_text(
        json.dumps({"sha256": hashes(), "scope": CONFIG["name"]}, indent=2) + "\n"
    )
    with zipfile.ZipFile(OUTPUT / "source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for file in files():
            archive.write(file, file.relative_to(ROOT))
    print("Packaged this project only; credentials, other projects and runtime excluded.")


def build() -> None:
    (ROOT / ".tools").mkdir(exist_ok=True)
    if PROJECT == "tire":
        importlib.import_module("tire_demo.cli").export_artifacts()
    else:
        module = importlib.import_module("solution_labs.evaluation")
        result = module.evaluation(PROJECT)
        (OUTPUT / "evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
        table = "\n".join(
            f"| {r['scenario']} | {'PASS' if r['passed'] else 'FAIL'} | {r['p50_ms']} | {r['p95_ms']} |"
            for r in result["scenarios"]
        )
        (OUTPUT / "evaluation.md").write_text(
            f"# Executed standalone synthetic evaluation\n\n{result['method']}\n\n| Case | Result | p50 ms | p95 ms |\n| --- | --- | --- | --- |\n{table}\n\nNo client outcomes or cloud performance are measured.\n"
        )
    (OUTPUT / "openapi.json").write_text(json.dumps(schema(), indent=2) + "\n")
    package()


def check() -> None:
    assert json.loads((OUTPUT / "manifest.json").read_text())["sha256"] == hashes(), (
        "Stale manifest"
    )
    assert json.loads((OUTPUT / "openapi.json").read_text()) == schema(), "API contract drift"
    result = json.loads((OUTPUT / "evaluation.json").read_text())
    assert result["passed"], "Scenario evaluation failed"
    if PROJECT == "tire":
        fingerprint = str(importlib.import_module("tire_demo.cli").implementation_fingerprint())
    else:
        fingerprint = importlib.import_module("solution_labs.evaluation").fingerprint()
    assert result["implementation_fingerprint"] == fingerprint, (
        "Regenerate evaluation after changes"
    )
    assert len(list(OUTPUT.glob("*.svg"))) == 5, "Five architecture/flow diagrams required"
    for file in OUTPUT.glob("*.svg"):
        ElementTree.parse(file)  # noqa: S314 - generated local diagram
    for name in ["source.zip", "walkthrough.mp4", "walkthrough.vtt", "review.md"]:
        assert (OUTPUT / name).is_file(), f"Missing evidence: {name}"
    for page in (ROOT / "dist").rglob("*.html"):
        for link in re.findall(r'(?:href|src)="([^"?#]+)', page.read_text()):
            if ":" in link or link.startswith("/"):
                continue
            target = (page.parent / link).resolve()
            assert target.is_file() or (target / "index.html").is_file(), (
                f"Broken local link: {page.name} → {link}"
            )
    with zipfile.ZipFile(OUTPUT / "source.zip") as archive:
        expected = {str(file.relative_to(ROOT)) for file in files()}
        assert set(archive.namelist()) == expected, "Source package scope mismatch"
        for file in files():
            assert archive.read(str(file.relative_to(ROOT))) == file.read_bytes(), (
                "Source download is stale"
            )
    print("Standalone evidence, API, fingerprints, links and scoped source passed.")


def secrets() -> None:
    rules = [
        re.compile(r"-----BEGIN (?:RSA |EC |ENCRYPTED )?PRIVATE KEY-----"),
        re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
        re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    ]
    failures = []
    for file in files():
        if file.suffix in {".mp4", ".png", ".jpg", ".pdf", ".zip"}:
            continue
        if any(rule.search(file.read_text(errors="ignore")) for rule in rules):
            failures.append(str(file.relative_to(ROOT)))
    assert not failures, "Potential credentials: " + ", ".join(failures)
    print("Secret-pattern scan passed; GitHub Actions also runs Gitleaks.")


if __name__ == "__main__":
    {"build": build, "package": package, "check": check, "secrets": secrets}[sys.argv[1]]()
