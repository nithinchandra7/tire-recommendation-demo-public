# ADR 03 — Timestamped stock and idempotent updates

Status: accepted for the local implementation.

Context: stale or duplicated source events can misrepresent availability. Conversation history cannot establish stock freshness.

Decision: persist quantity and observation time independently of preferences. Stable event IDs and canonical payloads identify retries. A duplicate is ignored; reuse of an ID with different content is a conflict. Only a strictly newer observation changes stock. Event outcome and inventory updates commit atomically.

The query excludes observations older than 30 minutes and future-dated records. It requires the requested quantity at one location; combining quantities across warehouses is a separate fulfillment capability.

Tradeoff: excluding stale stock can reduce available options. The UI communicates observation age and can offer fresh alternatives. It does not promise reservations, delivery guarantees or physically real-time stock.

Verification: replay, conflicting IDs, out-of-order observations, future observations, insufficient quantity and stale-local-stock cases. Cloud ingestion requires equivalent MERGE semantics and data-quality checks, because ordinary Snowflake primary/foreign keys are not enforcement substitutes.
