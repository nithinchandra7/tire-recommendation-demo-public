# Security boundaries

This repository contains synthetic local demonstrations. Bind the Python service to 127.0.0.1. A loopback-peer, local-host and same-origin boundary rejects remote clients and cross-site browser requests before simulated identity headers are accepted. These headers are not production authentication. Do not expose the simulator through a public reverse proxy or attach real customer data. Production deployment requires real authentication, server-derived authorization, visitor isolation and abuse controls.

Dependency locks include hashes and patched security floors. CI audits Python and npm dependencies on changes and weekly; Dependabot maintains packages and immutable GitHub Action pins. Rebuild public source downloads after changing dependencies or application code.

For a potential security issue, contact the portfolio owner privately using the contact details at https://nithinchandra.com. Do not include credentials or private datasets in public issues.
