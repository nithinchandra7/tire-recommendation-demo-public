# Architecture and implemented boundaries

## Local runtime

Browser UI → FastAPI → typed preferences and simulated retailer scope → parameterized SQLite SQL → eligible ranked evidence → authorized product descriptions → factual explanations → UI.

Components: Pydantic request/response boundaries; persisted SQLite sessions and inventory events; scoped SQL recommendation engine; bounded request traces; native SVG architecture explorer. SQLite and Snowflake implement the same query interface. The shared SQL uses epoch observation times and fixed normalized features. Snowflake named bindings are translated to connector pyformat bindings; data values remain parameters.

The recommendation query performs scope restriction, hard eligibility checks, stock freshness/quantity checks and weighted ranking in one SQL execution. Those operations share one measured query duration. Other queries resolve scope, location, fitment, above-budget upgrades and product facts. Total request timing includes them and state persistence.

## Data contracts

PRODUCT: product_id, size, minimum load/speed properties, season, positive price, illustrative comfort/wet ratings, warranty, description.

VEHICLE: illustrative sample vehicle, assigned size, minimum load/speed requirements and fitment version. These records illustrate the contract; VIN decoding alone cannot establish fitment. A real deployment requires a separately approved fitment source.

INVENTORY: product/location composite key, nonnegative quantity and source observation epoch. Maximum accepted age is 30 minutes by default. Future-dated observations are rejected. Availability is not reservation or a guarantee of order fulfillment.

RETAILER_SCOPE: assigned locations. Browser-selected store IDs never extend that server-defined scope.

RESPONSE: unique product recommendations, score contributions, optional upgrade identified as above budget, stock timestamps, owned session/revision, request trace, data/rules versions and explanation provenance.

## Preference handling

Typed form filters are authoritative. A follow-up merges supported comfort, wet-grip, price and season preferences before the query. Unsupported text leaves filters intact and reports that it was not interpreted. Missing filters on an owned existing session retain that session's current filters. Conflicting fitment size is rejected; users can choose size-only mode explicitly. Minimum vehicle specifications cannot be lowered through preferences.

## SQL and AI responsibilities

SQL establishes eligibility and ranking. The local knowledge path is an exact, scope-constrained product-description lookup, not vector search. Templates render values from selected records. Optional Foundry Azure OpenAI or Snowflake AI_COMPLETE adapters return only validated explanation-emphasis keys. They cannot return executable SQL, change candidate order or supply factual claims. Errors fall back to factual templates.

Cortex Search is an optional reference extension. It uses owner rights; source-table permissions do not automatically constrain a caller's search results. Derive audience filters server-side or isolate audience indexes and deny direct retailer access to a broad index. Product-roadmap or other restricted knowledge must remain isolated.

## Cloud deployment mapping

Snowflake: catalog, inventory, approved fitment, retailer-scope tables, governed serving queries and warehouse-side ranking. Azure: container-hosted UI/API, source ingestion, verified Entra token-to-retailer scope mapping, Key Vault and monitoring. Foundry or Cortex can supply optional bounded inference.

Cloud deployment requires replacing simulated identity and single-instance local session state. Use a shared managed state store for multiple API replicas. The Docker image is a local/container demonstration, not a production-ready authentication deployment. The Azure guide describes these missing bindings.

## Reference sources

- Snowflake connector: https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect
- Cortex Search rights: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview
- AI_COMPLETE: https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-string
- Azure Container Apps identity: https://learn.microsoft.com/en-us/azure/container-apps/managed-identity
- Foundry Azure OpenAI JSON mode: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/json-mode
