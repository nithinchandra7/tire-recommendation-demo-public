(function () {
  const nodes = [
    [
      "seed",
      30,
      30,
      "SYNTHETIC FIXTURES",
      "Catalog & inventory",
      "Fixed seed · illustrative fitment",
      "Generator creates 400 fictional products, 8 locations, 5 sample vehicles and 3,200 stock observations. No client data is used.",
    ],
    [
      "load",
      315,
      30,
      "DATA PREPARATION",
      "Validate & load",
      "Constraints · idempotent events",
      "Validate keys and specifications. Initial seeding is repeatable; inventory event IDs prevent duplicate application and older timestamps cannot replace newer stock.",
    ],
    [
      "sql",
      600,
      30,
      "SQLITE / SQL",
      "Decision data layer",
      "Eligibility · inventory · ranking",
      "One parameterized SQL query enforces scope, size, minimum specifications, quantity, freshness and delivery. Fixed normalized features and explicit weights rank eligible options.",
    ],
    [
      "ui",
      30,
      240,
      "BROWSER",
      "Retailer workspace",
      "Find · compare · refine",
      "An accessible retailer interface displays compatible products, available quantity, lead times, observation age, optional upgrades and per-factor evidence.",
    ],
    [
      "api",
      315,
      240,
      "PYTHON / FASTAPI",
      "Request orchestration",
      "Validate · scope · query",
      "Pydantic validates requests. The API resolves a server-defined simulated retailer scope, merges preferences, resolves sample fitment and calls the SQL layer. Entra authentication is a separate cloud reference boundary.",
    ],
    [
      "facts",
      890,
      30,
      "SCOPED SQL LOOKUP",
      "Product knowledge",
      "Approved candidate facts",
      "Fetch descriptions only for already selected product IDs and within the retailer's inventory scope. Local retrieval is an exact SQL lookup; Cortex Search is a reference extension, not an implemented vector index.",
    ],
    [
      "explain",
      890,
      240,
      "FACT-BASED TEMPLATES",
      "Explanation boundary",
      "Facts · citations · fallback",
      "Numerical and product statements are rendered by application code. Optional models return only validated emphasis keys. Failure falls back to templates and never changes eligibility or ordering.",
    ],
    [
      "state",
      315,
      450,
      "LOCAL SQLITE",
      "Preference state",
      "Retailer owner · revision",
      "Store typed filter state by session and retailer. Follow-up preferences merge before querying. Local persisted state is suitable for a single-instance demo; cloud deployment needs a shared state backend.",
    ],
    [
      "telemetry",
      600,
      450,
      "REQUEST TRACES",
      "Evidence & operations",
      "Measured timing · versions",
      "Record query and explanation timing, scope, filter revision, rule/data versions, returned candidate counts and request-local scenario overrides. Trace access is scoped and memory is bounded.",
    ],
  ].map(([id, x, y, platform, title, sub, detail]) => ({
    id,
    x,
    y,
    w: 230,
    h: 114,
    platform,
    title,
    sub,
    detail,
  }));
  const cloud = {
    seed: [
      "AZURE / SOURCE REFERENCE",
      "Product & inventory feeds",
      "Source contracts · timestamps",
    ],
    load: [
      "AZURE INGESTION REFERENCE",
      "Validate & publish updates",
      "Idempotent Snowflake loading",
    ],
    sql: [
      "SNOWFLAKE",
      "Governed SQL decisioning",
      "Serving views · warehouse query",
    ],
    ui: [
      "AZURE CUSTOM APPLICATION",
      "Retailer workspace",
      "Container-hosted UI reference",
    ],
    api: [
      "AZURE CONTAINER APPS",
      "Python API / FastAPI",
      "Entra scope · typed requests",
    ],
    facts: [
      "SNOWFLAKE SQL / SEARCH OPTION",
      "Scoped product knowledge",
      "Search requires audience isolation",
    ],
    explain: [
      "CORTEX OR FOUNDRY OPTION",
      "Bounded model selection",
      "Validated emphasis keys",
    ],
    state: [
      "SHARED STATE REFERENCE",
      "Preference state",
      "Replace single-instance SQLite",
    ],
    telemetry: [
      "AZURE MONITOR REFERENCE",
      "Traces & operations",
      "Managed identity · Key Vault",
    ],
  };
  const paths = [
    [null, "data", "seed", "load", "Synthetic source records"],
    [
      "M545 50L600 50",
      "data",
      "load",
      "sql",
      "Validated catalog and inventory",
    ],
    [null, "request", "ui", "api", "Typed requirements and follow-up"],
    [null, "data", "api", "ui", "Ranked options and stock timestamps"],
    [
      null,
      "request",
      "api",
      "sql",
      "Scoped parameterized recommendation query",
    ],
    [null, "data", "sql", "api", "Eligible ranked product evidence"],
    [null, "request", "api", "state", "Read and persist owned session state"],
    [null, "data", "state", "api", "Typed preferences and revision"],
    [null, "request", "api", "facts", "Retrieve approved candidate facts"],
    [null, "data", "sql", "facts", "Scope-constrained product records"],
    [null, "data", "facts", "api", "Authorized product context"],
    [null, "request", "api", "explain", "Bounded evidence for explanation"],
    [null, "data", "explain", "api", "Verified-fact explanation or fallback"],
    [null, "context", "api", "telemetry", "Request trace and versions"],
  ];
  function model(mode) {
    return {
      label: `Tire demo ${mode} architecture`,
      width: 1150,
      height: 605,
      nodes: nodes.map((n) =>
        mode === "cloud"
          ? {
              ...n,
              platform: cloud[n.id][0],
              title: cloud[n.id][1],
              sub: cloud[n.id][2],
              reference: true,
            }
          : { ...n },
      ),
      paths,
    };
  }
  window.tireArchitecture = { model };
})();
