# Review and verification record

Status: independent implementation review completed, findings addressed, and local verification passed on October 11, 2026. The reviewer reported no remaining blockers for the local demonstration after the second review.

Review scope: eligibility/ranking correctness, scope boundaries, state transitions, inventory ordering, model fallbacks, SQL binding, diagram fidelity, provenance, developer checks and evidence completeness.

## Findings and fixes

| Finding | Resolution |
|---|---|
| Snowflake decimal values could enter ranking/JSON unchanged | Normalize numeric values at the adapter boundary and reject non-finite numbers |
| Optional Cortex/Foundry failures could interrupt recommendations | Preserve deterministic recommendations and fall back to factual templates |
| Concurrent preference updates could overwrite state | Compare-and-swap revisions with a 409 conflict response |
| Negated or competing preferences could be interpreted incorrectly | Require clarification rather than silently changing priorities |
| Refinement timing did not reflect useful work | Measure the actual scoped refinement/query/explanation stages |
| Model emphasis selection did not change the explanation | Restrict the model to allowed keys and use those keys to select factual clauses |
| Inventory observations from the future were ambiguous | Enforce a strict as-of upper bound |
| Setup omitted installation of the local package | Document and verify both developer and non-editable native installation |
| Cloud data quality predicates missed NULL values | Add explicit NULL conditions with a meaningful regression test |

## Verification results

- 42 Python tests passed; one opt-in live Snowflake test skipped because no account is configured.
- Four JavaScript tests passed. Backend statement coverage: 95.73%, above the required 90%.
- Ruff lint/format, strict mypy, ESLint, Prettier, secret-pattern checks and evidence checks passed.
- Six existing architecture graphs (146 routed edges) and two demo maps passed endpoint/clearance checks. Five demo SVG exports match the renderer.
- Native HTTP smoke passed: startup, profile/demo, scoped recommendations, refinement, trace isolation and all 25 evidence downloads.
- Fresh virtual environment verification passed using hashed runtime dependencies and a non-editable wheel built from the exported source archive. Import resolved to site-packages. No Docker was used.
- Python runtime/developer/cloud dependency audits and npm audit reported no known vulnerabilities at verification time.
- Desktop/mobile browser checks covered recommendation scenarios, comparison, refinement, architecture highlighting and the captioned 120-second walkthrough.
- Pre-commit and full pre-push checks are installed locally; CI configuration repeats the native suite without a Docker requirement.
- Evidence manifest hashes are regenerated with the source package and checked for drift.

## Verification limits

Snowflake, Azure and live model execution have not been verified. The optional Docker image was not built. GitHub CI is prepared but has not run on a remote repository. Local simulated retailer identity and single-instance SQLite state must be replaced before public production deployment. The walkthrough is a rendered video of actual synthetic outputs, not the original client application or a recording of the retailer UI. Original engagement outcomes remain user-provided facts rather than measurements from this independent demonstration.

One non-blocking test dependency warning remains: Starlette reports deprecation of its current HTTPX test-client integration. The installed locked versions pass the suite.

## Standalone repository verification

The split was verified on October 12, 2026 using a fresh non-editable Python install and npm ci. 42 Python tests passed with 95.73% coverage; the optional live tire cloud test remains skipped. Formatting, lint, strict types, JavaScript architecture tests, scoped source/archive checks, regenerated API/evaluation fingerprints and native HTTP startup/download checks passed. GitHub Actions results are reported separately after pushing.
