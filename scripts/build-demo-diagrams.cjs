const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const context = vm.createContext({ window: {} });
for (const file of [
  "dist/technical-graph.js",
  "dist/tire-demo/architecture.js",
]) {
  vm.runInContext(fs.readFileSync(path.join(root, file), "utf8"), context);
}
const graph = context.window.diagramGraph;
const escape = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const directory = path.join(root, "dist/tire-demo/artifacts");
fs.mkdirSync(directory, { recursive: true });
function writeArtifact(name, svg) {
  const file = path.join(directory, name);
  if (process.argv.includes("--check")) {
    if (!fs.existsSync(file) || fs.readFileSync(file, "utf8") !== svg)
      throw new Error(`Regenerate ${name}`);
  } else fs.writeFileSync(file, svg);
}
for (const mode of ["local", "cloud"]) {
  const model = context.window.tireArchitecture.model(mode);
  graph.validate(model);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${model.width} ${model.height + 80}"><title>${escape(model.label)}</title><style>text{font-family:Arial;fill:#192d26}.platform{font-size:9px;fill:#69716a}.title{font-size:15px}.sub{font-size:9px;fill:#69716a}.wire{fill:none;stroke:#73886a;stroke-width:1.5}.request{stroke-dasharray:6 4}.context{stroke-dasharray:2 4}</style><rect width="100%" height="100%" fill="#f6f5ef"/><defs>${graph.markers("arrow", "#73886a", 9)}</defs><g transform="translate(0 55)">${model.paths.map((p) => `<path d="${graph.route(model, p)}" class="wire ${p[1]}" marker-end="url(#arrow)"><title>${escape(p[4])}</title></path>`).join("")}${model.nodes.map((n) => `<g><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="6" fill="#edf0e5" stroke="#b7c5ad"${mode === "cloud" ? ' stroke-dasharray="5 3"' : ""}/><text class="platform" x="${n.x + 15}" y="${n.y + 24}">${escape(n.platform)}</text><text class="title" x="${n.x + 15}" y="${n.y + 56}">${escape(n.title)}</text><text class="sub" x="${n.x + 15}" y="${n.y + 90}">${escape(n.sub)}</text></g>`).join("")}</g><text x="30" y="28" font-size="18">${mode === "local" ? "Implemented local demonstration" : "Snowflake / Azure reference deployment"}</text><text x="30" y="660" font-size="10">Independent demonstration · synthetic data · cloud bindings require configuration</text></svg>`;
  writeArtifact(`${mode}-architecture.svg`, svg);
}
const rows = {
  "runtime-sequence": [
    "Recommendation request",
    [
      "Retailer UI → API: typed requirements + simulated scope",
      "API → State: load and merge owned preferences",
      "API → SQL: scoped eligibility, availability and ranking",
      "SQL → API: candidates + observation times + score contributions",
      "API → Product lookup: authorized candidate descriptions",
      "API → Explanation: template or validated model emphasis",
      "API → State / Trace: persist revision and request evidence",
      "API → UI: alternatives, optional upgrade and facts",
    ],
  ],
  "ingestion-flow": [
    "Inventory event flow",
    [
      "Synthetic source emits stable event ID + product/location key",
      "Validate quantity, observation time and assigned scope",
      "Begin atomic transaction",
      "Existing event ID + same payload → duplicate (no change)",
      "Existing event ID + different payload → conflict",
      "Observation newer than stored → apply quantity and timestamp",
      "Older / equal observation → ignore; record outcome",
      "Commit event outcome and inventory together",
    ],
  ],
  "data-model": [
    "Logical data model",
    [
      "PRODUCT (product_id PK): size, load/speed, price, attributes",
      "VEHICLE (vehicle_id PK): illustrative size + minimum specs + version",
      "LOCATION (store_id PK): coordinates, kind, delivery estimate",
      "INVENTORY (product_id + store_id PK): quantity + observation epoch",
      "RETAILER_SCOPE (retailer_id + store_id PK): assigned locations",
      "SESSION_STATE (session_id PK): retailer owner, filter JSON, revision",
      "INVENTORY_EVENT (event_id PK): canonical payload + outcome",
      "Product/location keys connect stock; scope constrains every query",
    ],
  ],
};
for (const [name, [title, steps]] of Object.entries(rows)) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 730"><title>${escape(title)}</title><rect width="1100" height="730" fill="#f6f5ef"/><text x="40" y="45" font-family="Arial" font-size="24" fill="#192d26">${escape(title)}</text>${steps.map((s, i) => `<rect x="40" y="${75 + i * 75}" width="1010" height="55" rx="5" fill="${i % 2 ? "#edf0e5" : "#fbfaf6"}" stroke="#cbd4c0"/><text x="60" y="${109 + i * 75}" font-family="Arial" font-size="15" fill="#192d26">${String(i + 1).padStart(2, "0")}  ${escape(s)}</text>${i < steps.length - 1 ? `<path d="M550 ${130 + i * 75}v18m-4-4l4 4 4-4" fill="none" stroke="#73886a"/>` : ""}`).join("")}<text x="40" y="710" font-family="Arial" font-size="11" fill="#69716a">Independent implementation · all records and fitment requirements are synthetic</text></svg>`;
  writeArtifact(`${name}.svg`, svg);
}
console.log("Generated and validated five native SVG diagrams.");
