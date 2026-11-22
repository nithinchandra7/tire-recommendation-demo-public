# Local scenario evaluation

Dataset: synthetic-v1-seed-7.

20 sequential runs per scenario including persistence; p95 is nearest-rank.

400 products; 8 locations; 3,200 inventory observations. SQLite + factual templates.

| Scenario | Checks | p50 ms | p95 ms |
|---|---|---:|---:|
| standard | PASS | 6.662 | 7.207 |
| nearby | PASS | 6.156 | 7.69 |
| quantity | PASS | 6.831 | 8.032 |
| stale | PASS | 6.036 | 6.775 |
| no_match | PASS | 2.028 | 2.352 |
| upgrade | PASS | 6.322 | 6.55 |

## Measurement limits

Local synthetic workload only. Snowflake, Azure, cloud models and production outcomes are not measured.

Latency includes query, lookups, explanation and state persistence. No production SLA is claimed.

A passing scenario check is not an independent verification of the original client engagement.
