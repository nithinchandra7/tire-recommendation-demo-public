# Two-minute visual walkthrough

Format: rendered technical walkthrough using actual synthetic API outputs, with English captions. No client screenshots, original implementation recording, voice impersonation or production outcome claims.

| Time | Visual | Caption / reasoning |
|---|---|---|
| 00:00–00:20 | Typed sample sedan requirements and flow | Four compatible tires, a $150 budget, three-day lead time and explicit preferences. All data is fictional. |
| 00:20–00:40 | Actual standard-scenario product cards | SQL filters compatibility and fresh stock, then ranks eligible options. Show real synthetic prices, locations and scores. |
| 00:40–01:00 | Nearby-stock scenario output | Local stock is unavailable in this request. Alternatives come from another permitted location. |
| 01:00–01:20 | Actual preference transition | Refine to quieter tires under $140. Typed preferences merge before the query; inspect changed ranking and state revision. |
| 01:20–01:40 | Stale-stock scenario and execution evidence | Old observations are excluded. Contributions explain the score; timing is measured rather than invented. |
| 01:40–02:00 | Local / cloud boundary and evidence package | Local SQLite/FastAPI behavior is implemented. Snowflake/Azure connections need configuration. Inspect code, diagrams, decisions and evaluations. |

Live demo shortcut: the walkthrough tab's guided-demo button runs the nearby-stock scenario and opens its execution inspector. The video export visualizes results from the backend; it is not a screen recording of the retailer UI.
