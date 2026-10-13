# Snowflake configuration and validation

All connection values in .env.example are placeholders. The agent does not provision resources, load records or run billable warehouse/model queries without account configuration. Default DATA_BACKEND=sqlite and AI_PROVIDER=template require no account.

## Configure a dedicated sandbox

1. Install requirements-cloud.lock and the application package.
2. Use a dedicated existing warehouse/database/schema and least-privilege service user. Configure key-pair authentication through your Snowflake administrator; keep private keys outside the repository.
3. Set SNOWFLAKE_ACCOUNT, USER, ROLE, WAREHOUSE, DATABASE, SCHEMA and PRIVATE_KEY_PATH in an ignored .env file or managed environment. The role/resource identifiers are validated.
4. Review and execute tire-demo/sql/snowflake/schema.sql only in that dedicated sandbox. Primary/foreign key declarations on ordinary Snowflake tables do not replace quality checks.
5. Load the synthetic CSVs from tire-demo/data into matching tables using your approved loading method. Preserve source observation epochs or explicitly regenerate fresh synthetic inventory for the current time. Dates from the fixed local demonstration clock are intentionally stale outside that clock.
6. Select DATA_BACKEND=snowflake and run make demo. Warehouse execution uses current UTC time, not the frozen local demo clock.
7. Explicitly enable SNOWFLAKE_TEST_ENABLED=1 and run the cloud test. It validates read-only connectivity; inspect full functional query behavior separately after loading the sandbox.

No actual account identifier, key, password or token is committed. Required placeholder values fail validation before connection. Connector timeouts and QUERY_TAG isolate the demonstration's work for inspection. End users have no direct warehouse credentials.

## Optional inference

AI_PROVIDER=cortex requires CORTEX_MODEL, the Snowflake connector and suitable model privileges. AI_PROVIDER=foundry uses an Azure OpenAI deployment accessible through Foundry and requires AZURE_OPENAI_ENDPOINT, DEPLOYMENT and API_KEY. It uses the v1 chat-completions route. Model output is restricted to emphasis keys and validated; facts remain rendered by code. Cloud inference has not been exercised without credentials.

## Verification distinction

Passing mock adapter tests demonstrates connection/configuration/binding behavior. It does not establish live SQL execution, permissions, throughput, model availability or production readiness. Cloud test skips are reported explicitly.
