# Azure reference deployment

The verified local path is Python + SQLite without Docker. Azure service bindings below are reference designs and have not been provisioned.

## Source deployment alternative

Azure App Service for Linux supports Python/FastAPI apps deployed from source or ZIP without building a custom container locally. This is an alternative host for the same UI/API boundary shown as Container Apps in the cloud diagram; do not deploy both hosts for this small demo.

Keep the repository layout and install the Python package plus locked runtime dependencies during the platform build. Set the working directory/TIRE_DEMO_ROOT to the extracted application root so SQL and static assets resolve. Configure a FastAPI-compatible startup process bound to the platform port, rather than the loopback-only local command. A public deployment still needs real authentication, managed state, secure configuration and cloud verification described below. No App Service resource has been created by this task.

Official source-deployment guide: https://learn.microsoft.com/en-us/azure/app-service/quickstart-python

## Optional container deployment

The Dockerfile is retained as an optional artifact. Building a container is not required to run, review or test this project, and the image has not been verified here.

## Components

- Azure Container Apps hosts the UI and Python API behind one origin.
- Microsoft Entra authenticates retailers. Validate token signature, issuer, audience, expiry and tenant; resolve retailer/store scope from a trusted server-side mapping. Replace the local X-Demo-Retailer simulation before exposing a real service.
- Managed identity accesses Key Vault and supported Azure dependencies. Store Snowflake key material securely; an Azure identity does not automatically grant Snowflake access.
- A shared managed state store replaces local SQLite sessions for multiple replicas. Separate catalog caching from changing inventory. Keep state revisions and tenant ownership.
- Azure ingestion receives source product/inventory updates and stages validated events for Snowflake. Feed timestamps, source IDs and replay behavior must be part of the source contract.
- Azure Monitor/Application Insights tracks request IDs, query/model timing, dependency failures, freshness and no-result rates. Avoid secrets and sensitive customer text in logs.
- Optional Foundry model deployments support bounded explanation emphasis. Cortex remains a Snowflake service, reached through the Snowflake adapter.

## Developer sequence

First run make check and make audit without Docker. If selecting App Service, use the platform's Python source/ZIP deployment workflow. If selecting Container Apps, build/test the optional image in an environment with a container builder. Then configure identity/secrets and the dedicated Snowflake sandbox; replace simulated identity and single-instance state; validate authorization, health/readiness and inventory failure behavior before public exposure. This portfolio task remains local-only.

Placeholders: subscription ID, resource group, container-app name, Entra tenant/client IDs and Key Vault URI appear in .env.example. The current application does not claim these reference integrations are active. Live platform scaling, private connectivity and cost limits require environment-specific decisions and measurement.

Official references:

- https://learn.microsoft.com/en-us/azure/container-apps/managed-identity
- https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets
- https://docs.snowflake.com/en/user-guide/privatelink-azure
