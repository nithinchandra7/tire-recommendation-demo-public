# ADR 01 — Deterministic eligibility and bounded explanations

Status: accepted for the independent demo.

Context: retailers need compatible products with sufficient fresh stock. A plausible model answer is insufficient evidence of compatibility or availability.

Options: model-generated SQL/free-form recommendations; deterministic queries with unrestricted generated explanations; deterministic queries with fact rendering and bounded model emphasis.

Decision: use parameterized SQL for hard constraints and ranking. Optional models return only allowlisted emphasis keys. Application code renders prices, stock, product ratings and citations from selected rows.

Tradeoff: explanations are less flexible than free-form generation. Correctness and inspectability are stronger; model outages preserve recommendations.

Verification: invalid model fields/JSON, provider exceptions, incompatible specs, conflicting fitment and injected preference text cannot bypass the constraints. Synthetic fitment is clearly labeled and never represented as manufacturer-approved data.
