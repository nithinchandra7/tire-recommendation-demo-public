# ADR 04 — Explainable scoring and optional upgrades

Status: accepted; weights illustrate business choices and are not learned from client behavior.

Decision: score eligible candidates using comfort, wet grip, price, proximity and delivery. Each priority has fixed weights summing to one. Comfort and wet grip use illustrative 1–10 attributes; price is normalized against the accepted budget; proximity against a fixed 75-mile range; delivery against a fixed 15-day range. The current UI accepts up to 7 days and the API up to 14.

Stable ordering: descending total score, then ascending price, product ID and location ID. Pick the best eligible location per product before showing six distinct products. Show the contribution of every factor.

Upgrades are queried separately using a maximum 25% budget increase. They must improve at least one of comfort/wet grip without degrading the other compared with the best current match. All fitment, stock and freshness constraints remain. They are labeled above budget and are not silently added to the main result set. Their scores are not compared with scores normalized to the original budget.

Tradeoff: transparent weights are easy to inspect but need real stakeholder calibration. Synthetic scores are not evidence of measured conversion uplift or real tire performance. Margin optimization and multi-location fulfillment are extensions.
