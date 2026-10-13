PYTHON ?= .venv/bin/python
NPM ?= npm
NODE ?= node
PORT ?= 4191

.PHONY: setup demo quick check artifacts package smoke audit hooks
setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.lock
	.venv/bin/pip install --no-deps --no-build-isolation .
	$(NPM) ci
demo: package
	$(PYTHON) -m uvicorn tire_demo.app:app --host 127.0.0.1 --port $(PORT)
quick:
	.venv/bin/ruff check tire-demo/src tire-demo/tests scripts
	.venv/bin/ruff format --check tire-demo/src tire-demo/tests scripts
	$(NPM) run lint
	$(NPM) run format:check
	$(PYTHON) scripts/evidence.py secrets
check: package quick
	.venv/bin/mypy
	$(PYTHON) -m pytest --junitxml=runtime/test-results.xml
	$(NPM) test
	$(NPM) run architecture
	$(PYTHON) scripts/evidence.py check
	$(MAKE) smoke
artifacts:
	$(NODE) scripts/build-demo-diagrams.cjs
	$(PYTHON) scripts/evidence.py build
package:
	$(PYTHON) scripts/evidence.py package
smoke:
	$(PYTHON) scripts/smoke.py
audit:
	.venv/bin/pip-audit --cache-dir .tools/audit-cache --disable-pip --no-deps -r requirements-dev.lock
	.venv/bin/pip-audit --cache-dir .tools/audit-cache --disable-pip --no-deps -r requirements-cloud.lock
	$(NPM) audit --audit-level=high --cache .tools/npm-cache
hooks:
	.venv/bin/pre-commit install --hook-type pre-commit --hook-type pre-push
