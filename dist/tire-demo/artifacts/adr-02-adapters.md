# ADR 02 — Local reproducibility and a Snowflake adapter

Status: accepted; live Snowflake validation pending account configuration.

Context: portfolio visitors and developers should reproduce behavior without a client environment or cloud billing.

Options: Snowflake-only execution; browser-only simulated outputs; an actual local backend with a separately configurable warehouse adapter.

Decision: SQLite is the default execution backend. The Snowflake connector implements a query contract with pyformat value bindings, validated resource identifiers, key-pair authentication, query tagging and bounded connection/query timeouts. Shared SQL avoids dialect-specific time arithmetic by using source epochs.

Tradeoff: local contract tests and mock connector tests do not validate warehouse permissions, performance, deployed UDFs or live data. The optional cloud test is separately enabled and initially checks read-only connectivity. It does not provision or populate an account.

Verification: local constraints and bindings, generated SQL consistency, identifier rejection, connector lifecycle and explicit cloud skips. Snowflake setup and seeded data require developer execution in a dedicated sandbox.
