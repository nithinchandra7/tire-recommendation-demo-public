# Tire Recommendation Demo

Independent reconstruction with synthetic data. Original client work and this runnable demonstration are distinct; no client code, records or internal documents are included.

[Portfolio and original case study](https://nithinchandra.com) · [Source repository](https://github.com/nithinchandra7/tire-recommendation-demo-public)

## Run without Docker

From this repository's root, with Python 3.12+:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-deps .
.venv/bin/python scripts/evidence.py package
.venv/bin/python -m uvicorn tire_demo.app:app --host 127.0.0.1 --port 4191
```

Open http://127.0.0.1:4191/tire-demo/. API docs: http://127.0.0.1:4191/api/docs. Run from the repository root because SQL, static evidence and data resolve there. All Python imports come from this project's installed wheel; neither the portfolio nor another project is required.

## Developer workflow

With Python 3.12+ and Node 24+, run `make setup`, `make hooks`, `make check` and `make audit`. Setup uses a non-editable install: reinstall the project after changing Python source, before running tests or regenerating evidence. Git pre-commit runs formatting/lint and a secret-pattern scan; pre-push runs the complete suite. GitHub Actions repeats checks, dependency audits and Gitleaks. Cloud checks are explicitly opt-in/unverified; Docker is not required.

`make artifacts` regenerates diagrams, executed synthetic evaluations and API contracts. `make package` refreshes evidence hashes and the source download for this project alone. The captioned two-minute rendered walkthrough is included; its generation source is maintained in the integrated portfolio repository. Regenerate it there when visible demo outputs change.

## Scope and evidence

See [tire-demo/docs/architecture.md](tire-demo/docs/architecture.md), the four decision records, cloud setup, operations and review documents. The browser includes local/cloud diagrams with connected-component highlighting. Evidence contains five SVGs, OpenAPI, executed scenario outputs, evaluation timings, source and a captioned walkthrough. Local identities are simulated; this is a loopback demonstration, not an internet deployment.

Cloud account/workspace values remain placeholders in `.env.example` and the cloud guides. Never commit `.env`, private keys, tokens, client data or `runtime/`. Generated ZIP downloads, virtual environments and developer tools are ignored. No cloud deployment or production SLA is claimed.

## Relationship to the portfolio

This standalone repository is extracted from the reviewed integrated baseline `764057a`. The portfolio keeps a combined preview for presentation; each standalone owns its focused release and checks. Changes are synchronized deliberately, without automatic submodules or credentials. Review API/evidence drift and run both suites before copying changes between builds.

Security and local hosting: [Security boundaries](SECURITY.md).
