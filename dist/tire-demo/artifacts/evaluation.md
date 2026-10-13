# Local scenario evaluation

Dataset: synthetic-v1-seed-7.

20 sequential runs per scenario including persistence; p95 is nearest-rank.

400 products; 8 locations; 3,200 inventory observations. SQLite + factual templates.

| Scenario | Checks | p50 ms | p95 ms |
|---|---|---:|---:|
| standard | PASS | 4.708 | 5.239 |
| nearby | PASS | 4.292 | 4.792 |
| quantity | PASS | 4.001 | 4.168 |
| stale | PASS | 4.154 | 4.671 |
| no_match | PASS | 1.692 | 1.848 |
| upgrade | PASS | 4.739 | 5.236 |

## Measurement limits

Local synthetic workload only. Snowflake, Azure, cloud models and production outcomes are not measured.

Latency includes query, lookups, explanation and state persistence. No production SLA is claimed.

A passing scenario check is not an independent verification of the original client engagement.
