# Operations, failure behavior and troubleshooting

## Local operations

Run make demo from the repository root. The integrated preview binds to 127.0.0.1:4180. If the original static server at port 4173 is used, the retailer API is unavailable there; use the integrated preview for the working demo.

SQLite data and owned session state persist under runtime/. The seed loader does not overwrite an existing catalog. To reset, stop the server, move the runtime database to a backup, then restart. Scenario controls are request-local SQL overrides and do not alter stored inventory.

## Failure behavior

- No candidates: show the requirements and explicit choices to relax budget/delivery; never weaken fitment.
- Stale stock: exclude it and display observation age for returned alternatives.
- Scope violation: return 403 without broadening the store query.
- Unknown owned session/trace: return 404.
- Invalid request/fitment conflict: return 422.
- Data dependency error: return 503; logs include the exception class rather than credential-bearing details.
- Model invalid output/outage: return factual templates without changing results.
- Replayed stock event: no-op. Conflicting event payload: 409. Older event: ignored atomically.

## Measurement

Trace one actual SQL eligibility/inventory/ranking duration; separate lookup/explanation work and total request duration. Evaluation reports 20 local runs per scenario, median and nearest-rank p95, dataset scale and clock. These are observed demonstration timings, not production SLAs. Warehouse/model cost and concurrency must be measured in a configured deployment.

## Developer release checks

make check runs lint/format/type checks, unit/API tests, JavaScript tests, architecture regressions, artifact validity and secret patterns. make audit uses current vulnerability advisories and requires network access. CI repeats the checks and adds repository-wide secret scanning. Install hooks explicitly with make hooks.

The live Snowflake test is skipped by default. Cloud mock/contract tests remain part of the offline suite. Never report a missing-credential test as a successful live cloud check.
