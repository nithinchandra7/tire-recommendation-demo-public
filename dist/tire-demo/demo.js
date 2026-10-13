(function () {
  const { escape: e, money, comparisonRows } = window.tireHelpers;
  const $ = (selector) => document.querySelector(selector);
  let retailer = "north",
    session = null,
    options = null,
    result = null,
    selected = new Set();
  let architectureMode = "local",
    selectedComponent = "api",
    activeView = "workspace",
    controller = null,
    sequence = 0;
  const scenarioNotes = {
    standard:
      "Fresh stock, compatible products, and a balanced recommendation.",
    nearby:
      "This request simulates zero stock at the selected store. Search remains scoped to its network.",
    quantity:
      "This request simulates only two tires at the selected store. Four must come from another location.",
    stale:
      "The selected store's observation is two hours old. Its stock is excluded by the 30-minute freshness policy.",
    no_match:
      "A $60 budget demonstrates a no-result case. Compatibility and freshness remain enforced.",
    upgrade:
      "Explore a better product above budget, with the extra cost explicitly shown.",
  };
  async function api(path, body, signal) {
    const response = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Demo-Retailer": retailer,
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
      signal,
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Check the request values and try again.",
      );
    return data;
  }
  function notice(text, error = false) {
    $("#message").innerHTML = text
      ? `<div class="notice${error ? " error" : ""}">${e(text)}</div>`
      : "";
  }
  function view(id, focus = false) {
    activeView = id;
    document.querySelectorAll("[data-view]").forEach((button) => {
      const on = button.dataset.view === id;
      button.setAttribute("aria-selected", String(on));
      button.tabIndex = on ? 0 : -1;
      if (on && focus) button.focus();
    });
    document
      .querySelectorAll("main>section[role=tabpanel]")
      .forEach((panel) => {
        panel.hidden = panel.id !== id;
      });
  }
  function formFilters() {
    return {
      vehicle_id: $("#vehicle").value || null,
      size: $("#size").value,
      store_id: $("#store").value,
      quantity: Number($("#quantity").value),
      budget: Number($("#budget").value),
      season: $("#season").value,
      priority: $("#priority").value,
      max_lead_days: Number($("#lead").value),
      min_load_index: 98,
      min_speed_rank: 4,
    };
  }
  function applyFilters(filters) {
    $("#vehicle").value = filters.vehicle_id || "";
    $("#size").value = filters.size;
    $("#store").value = filters.store_id;
    $("#quantity").value = filters.quantity;
    $("#budget").value = filters.budget;
    $("#season").value = filters.season;
    $("#priority").value = filters.priority;
    $("#lead").value = String(filters.max_lead_days);
  }
  function card(product, index) {
    return `<article class="product-card"><div class="product-top"><div class="tire-icon" aria-hidden="true"></div><div><span class="rank-label">${index === 0 ? "BEST CURRENT MATCH" : `OPTION ${index + 1}`}</span><div class="spec">${e(product.tier)} · ${Number(product.score).toFixed(1)} pts</div></div></div><div class="product-body"><span class="product-brand">${e(product.brand)}</span><h3>${e(product.name)}</h3><div class="spec">${e(product.size)} · ${e(product.load_index)}${e(product.speed_symbol)}<br>${e(product.season)}</div><div class="product-price"><strong>${money(product.price)}</strong><span>/ tire</span></div><div class="stock"><strong>${e(product.available_quantity)} available</strong> · ${e(product.location_name)}<small>${product.lead_days === 0 ? "Pickup today" : `Estimated ${e(product.lead_days)} day(s)`} · ${e(product.distance)} mi away<br>Observed ${e(product.age_minutes)} min ago · synthetic clock</small></div><div class="attributes"><span>Comfort<strong>${e(product.comfort)} / 10</strong></span><span>Wet grip<strong>${e(product.wet_grip)} / 10</strong></span></div><details><summary>Why this option?</summary><p class="reasons">${e(product.explanation)}</p>${Object.entries(
      product.score_contributions,
    )
      .map(
        ([name, points]) =>
          `<div class="contribution"><span>${e(name)}</span><b>${Number(points).toFixed(1)} pts</b></div><div class="contribution-bar"><span style="width:${Math.min(100, Number(points) * 2)}%"></span></div>`,
      )
      .join(
        "",
      )}<p class="reasons">Source: ${e(product.citation)}<br>Illustrative ratings; score contributions sum to the displayed recommendation score.</p></details></div><button class="compare-button" data-compare="${e(product.product_id)}" aria-pressed="false">+ Add to comparison</button></article>`;
  }
  function renderResults(data) {
    result = data;
    session = data.session_id;
    selected.clear();
    applyFilters(data.filters);
    $("#follow-up").value = "";
    $("#follow-up-form").hidden = false;
    $("#run-meta").innerHTML =
      `Request ${e(data.trace.request_id.slice(0, 8))}<br>${Number(data.trace.total_ms).toFixed(1)} ms · ${e(data.explanation.mode)} explanations`;
    const changes = data.trace.preference_changes;
    notice(
      changes.length
        ? `Preference update: ${changes.join("; ")}`
        : $("#scenario").value === "standard"
          ? ""
          : scenarioNotes[$("#scenario").value],
    );
    $("#result-summary").innerHTML =
      `<div class="summary-line"><strong>${data.recommendations.length} distinct options · ${e(data.filters.size)}</strong><span>${e(data.trace.query_candidate_locations)} eligible product/location pairs</span></div>`;
    if (data.no_result) {
      $("#recommendations").innerHTML =
        `<div class="empty-state"><div class="tire-glyph" aria-hidden="true">◎</div><h3>${e(data.no_result.message)}</h3><p>${e(data.no_result.preserved)}</p><button id="increase-budget" class="secondary" style="margin-top:22px">Increase budget to $150 →</button></div>`;
    } else {
      $("#recommendations").innerHTML =
        `<div class="cards">${data.recommendations.slice(0, 3).map(card).join("")}</div>${
          data.recommendations.length > 3
            ? `<details class="more-results"><summary>Show ${data.recommendations.length - 3} more alternatives</summary><div class="cards">${data.recommendations
                .slice(3)
                .map((p, i) => card(p, i + 3))
                .join("")}</div></details>`
            : ""
        }`;
    }
    const premium = data.premium_option;
    $("#premium").innerHTML = premium
      ? `<article class="upgrade-card"><div><span class="eyebrow">OPTIONAL UPGRADE / ABOVE YOUR BUDGET</span><h3>${e(premium.brand)} ${e(premium.name)}</h3><p>Illustrative comfort ${e(premium.comfort)}/10 and wet grip ${e(premium.wet_grip)}/10. ${e(premium.available_quantity)} available at ${e(premium.location_name)}; estimated ${e(premium.lead_days)} day(s). Compatibility and freshness checks still apply.</p></div><div class="upgrade-price"><strong>${money(premium.price)}</strong><span>+${money(premium.extra_per_tire)} / tire<br>versus the best current match</span></div></article>`
      : "";
    $("#trace-time").textContent =
      `${Number(data.trace.total_ms).toFixed(1)} ms total`;
    $("#trace-content").innerHTML =
      `<span class="eyebrow">ACTUAL LOCAL EXECUTION / ${e(data.trace.request_id)}</span><div class="trace-stages">${data.trace.stages.map((s) => `<button data-trace-component="${e(s.component)}">${e(s.label)}<small>${Number(s.duration_ms).toFixed(3)} ms · inspect component ↗</small></button>`).join("")}</div><div class="trace-facts"><div><span>Hard constraints</span><b>${e(data.trace.hard_constraints.join(" · "))}</b></div><div><span>Retailer scope</span><b>${e(data.trace.retailer_scope.join(" · "))}</b></div><div><span>Data / rules versions</span><b>${e(data.trace.data_version)}<br>${e(data.trace.rules_version)}</b></div><div><span>State / clock</span><b>Filter revision ${e(data.revision)}<br>${e(data.trace.as_of)}</b></div></div><p class="small">SQL eligibility, inventory and ranking share one query timing. Total time includes all lookups and persistence. ${e(data.trace.simulation)}</p><button id="download-trace" class="secondary">Download execution JSON ↓</button>`;
    $("#compare-tray").hidden = true;
  }
  async function recommend(followUp = "") {
    if (!$("#recommend-form").reportValidity()) return;
    const current = ++sequence;
    if (controller) controller.abort();
    controller = new AbortController();
    const signal = controller.signal;
    $("#run").disabled = true;
    notice("Evaluating compatibility, inventory and preferences…");
    try {
      const body = {
        filters: formFilters(),
        scenario: $("#scenario").value,
        ...(session ? { session_id: session } : {}),
        follow_up: followUp,
      };
      const data = await api("/api/tire/recommendations", body, signal);
      if (current === sequence) renderResults(data);
    } catch (error) {
      if (error.name !== "AbortError" && current === sequence)
        notice(error.message, true);
    } finally {
      if (current === sequence) $("#run").disabled = false;
    }
  }
  async function loadOptions() {
    const data = await api("/api/tire/options");
    if (data.retailer !== retailer) return;
    options = data;
    $("#vehicle").innerHTML =
      data.vehicles
        .map((v) => `<option value="${e(v.vehicle_id)}">${e(v.name)}</option>`)
        .join("") + `<option value="">Size-only lookup</option>`;
    $("#size").innerHTML = data.sizes
      .map((s) => `<option>${e(s.size)}</option>`)
      .join("");
    $("#store").innerHTML = data.locations
      .map((l) => `<option value="${e(l.store_id)}">${e(l.name)}</option>`)
      .join("");
    $("#vehicle").value = "V01";
    $("#size").value = data.vehicles[0].size;
    $("#store").value = data.locations[0].store_id;
  }
  function renderArchitecture() {
    const model = window.tireArchitecture.model(architectureMode);
    const graph = window.diagramGraph;
    $("#map-key").innerHTML = graph.key();
    $("#map").innerHTML =
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${model.width} ${model.height}" data-connection-map="" role="group" aria-label="${e(model.label)}. Select a component to follow its connections."><defs>${graph.markers("demo-arrow", "#73886a", 9)}</defs>${model.paths.map((p) => `<path class="wire ${p[1]}" d="${graph.route(model, p)}" data-from="${p[2]}" data-to="${p[3]}" data-marker="demo-arrow" marker-end="url(#demo-arrow)"><title>${e(p[4])}</title></path>`).join("")}${model.nodes.map((n) => `<g class="arch-node${n.reference ? " reference" : ""}" data-node="${n.id}" data-component="${n.id}" role="button" tabindex="0" aria-pressed="false" aria-label="${e(n.title)}"><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="6"/><text class="platform" x="${n.x + 15}" y="${n.y + 24}">${e(n.platform)}</text><text class="title" x="${n.x + 15}" y="${n.y + 56}">${e(n.title)}</text><text class="subtitle" x="${n.x + 15}" y="${n.y + 90}">${e(n.sub)}</text></g>`).join("")}</svg>`;
    $("#component-select").innerHTML = model.nodes
      .map((n) => `<option value="${n.id}">${e(n.title)}</option>`)
      .join("");
    $("#architecture-download").href =
      `artifacts/${architectureMode}-architecture.svg`;
    $("#architecture-note").textContent =
      architectureMode === "local"
        ? "Implemented: local SQL lookup, SQLite state, FastAPI, factual templates, and measured traces. Optional cloud models are disabled by default."
        : "Reference deployment: Snowflake and Azure service bindings require configuration. Entra authentication, shared state and Azure ingestion/monitoring are deployment work; they are not running in this local demo. Cortex Search is an optional reference extension.";
    selectComponent(selectedComponent);
  }
  function selectComponent(id, focused = true) {
    selectedComponent = id;
    const model = window.tireArchitecture.model(architectureMode),
      node = model.nodes.find((n) => n.id === id);
    if (!node) return;
    $("#component-select").value = id;
    document.querySelectorAll("[data-node]").forEach((element) => {
      const on = element.dataset.node === id;
      element.classList.toggle("selected", on);
      element.setAttribute("aria-pressed", String(on));
    });
    window.diagramGraph.apply($("#map"), model, id, focused);
    const measured = result?.trace.stages.find((s) => s.component === id);
    $("#component-detail").innerHTML =
      `<div><span class="eyebrow">${architectureMode === "local" ? "IMPLEMENTED COMPONENT" : "REFERENCE CLOUD BINDING"}</span><h3 tabindex="-1">${e(node.title)}</h3></div><div><p>${e(node.detail)}</p>${measured ? `<p style="margin-top:12px">Last demo request: ${Number(measured.duration_ms).toFixed(3)} ms for “${e(measured.label)}”.</p>` : ""}</div>${window.diagramGraph.html(model, id, "data-connected-component")}`;
  }
  function compareToggle(id) {
    if (selected.has(id)) selected.delete(id);
    else if (selected.size < 3) selected.add(id);
    else {
      notice("Compare up to three products at a time.");
      return;
    }
    document.querySelectorAll("[data-compare]").forEach((button) => {
      const on = selected.has(button.dataset.compare);
      button.setAttribute("aria-pressed", String(on));
      button.textContent = on ? "✓ Added to comparison" : "+ Add to comparison";
    });
    $("#compare-tray").hidden = selected.size === 0;
    $("#compare-count").textContent = `${selected.size} selected · up to 3`;
    $("#compare-open").disabled = selected.size < 2;
  }
  $("#recommend-form").addEventListener("submit", (event) => {
    event.preventDefault();
    recommend();
  });
  $("#follow-up-form").addEventListener("submit", (event) => {
    event.preventDefault();
    recommend($("#follow-up").value);
  });
  $("#vehicle").addEventListener("change", () => {
    const vehicle = options?.vehicles.find(
      (v) => v.vehicle_id === $("#vehicle").value,
    );
    if (vehicle) $("#size").value = vehicle.size;
  });
  $("#size").addEventListener("change", () => {
    $("#vehicle").value = "";
  });
  $("#scenario").addEventListener("change", () => {
    $("#scenario-note").textContent = scenarioNotes[$("#scenario").value];
    $("#budget").value = $("#scenario").value === "no_match" ? 60 : 150;
    $("#quantity").value = 4;
    recommend();
  });
  $("#retailer").addEventListener("change", async () => {
    retailer = $("#retailer").value;
    session = null;
    ++sequence;
    if (controller) controller.abort();
    try {
      await loadOptions();
      await recommend();
    } catch (error) {
      notice(error.message, true);
    }
  });
  document.querySelector(".view-tabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-view]");
    if (button) view(button.dataset.view);
  });
  document.querySelector(".view-tabs").addEventListener("keydown", (event) => {
    const names = ["workspace", "architecture", "evidence", "walkthrough"];
    let index = names.indexOf(activeView);
    if (event.key === "ArrowRight") index = (index + 1) % 4;
    else if (event.key === "ArrowLeft") index = (index + 3) % 4;
    else if (event.key === "Home") index = 0;
    else if (event.key === "End") index = 3;
    else return;
    event.preventDefault();
    view(names[index], true);
  });
  $("#architecture-mode").addEventListener("change", () => {
    architectureMode = $("#architecture-mode").value;
    renderArchitecture();
  });
  $("#component-select").addEventListener("change", () =>
    selectComponent($("#component-select").value),
  );
  $("#map-reset").addEventListener("click", () =>
    selectComponent(selectedComponent, false),
  );
  $("#architecture").addEventListener("click", (event) => {
    const node = event.target.closest("[data-node]"),
      connection = event.target.closest("[data-connected-component]");
    if (node) selectComponent(node.dataset.node);
    if (connection) {
      selectComponent(connection.dataset.connectedComponent);
      $("#component-detail h3").focus({ preventScroll: true });
    }
  });
  $("#map").addEventListener("keydown", (event) => {
    const node = event.target.closest("[data-node]");
    if (node && ["Enter", " "].includes(event.key)) {
      event.preventDefault();
      selectComponent(node.dataset.node);
    }
  });
  $("#workspace").addEventListener("click", (event) => {
    const compare = event.target.closest("[data-compare]"),
      component = event.target.closest("[data-trace-component]");
    if (compare) compareToggle(compare.dataset.compare);
    if (component) {
      architectureMode = "local";
      $("#architecture-mode").value = "local";
      view("architecture");
      renderArchitecture();
      selectComponent(component.dataset.traceComponent);
    }
    if (event.target.closest("#increase-budget")) {
      $("#budget").value = 150;
      $("#scenario").value = "standard";
      $("#scenario-note").textContent = scenarioNotes.standard;
      recommend();
    }
    if (event.target.closest("#download-trace")) {
      const blob = new Blob([JSON.stringify(result.trace, null, 2)], {
          type: "application/json",
        }),
        link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `trace-${result.trace.request_id}.json`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    }
  });
  $("#compare-clear").addEventListener("click", () => {
    [...selected].forEach(compareToggle);
  });
  $("#compare-open").addEventListener("click", () => {
    const products = result.recommendations.filter((p) =>
      selected.has(p.product_id),
    );
    $("#comparison").innerHTML = `<table><tbody>${comparisonRows(products)
      .map(
        (row, index) =>
          `<tr>${row.map((cell, i) => (index === 0 || i === 0 ? `<th scope="${index === 0 ? "col" : "row"}">${e(cell)}</th>` : `<td>${e(cell)}</td>`)).join("")}</tr>`,
      )
      .join("")}</tbody></table>`;
    $("#compare-dialog").showModal();
  });
  $("#compare-close").addEventListener("click", () =>
    $("#compare-dialog").close(),
  );
  $("#guided-tour").addEventListener("click", async () => {
    view("workspace");
    $("#scenario").value = "nearby";
    $("#scenario-note").textContent = scenarioNotes.nearby;
    $("#budget").value = 150;
    await recommend();
    $("#trace-panel").open = true;
    notice(
      "Guided demo: local stock is unavailable, so compatible alternatives come from another permitted location. Open a product’s reasons, compare two options, then inspect the SQL component.",
    );
    $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  renderArchitecture();
  async function start() {
    try {
      const health = await api("/api/health");
      $("#runtime-status").textContent =
        `${health.backend.toUpperCase()} · ${health.provider} · API connected`;
      await loadOptions();
      await recommend();
    } catch {
      $("#runtime-status").textContent = "Integrated API is offline";
      notice(
        "Start the integrated preview with make demo, then open http://127.0.0.1:4180/tire-demo/. Architecture and evidence remain available here.",
        true,
      );
    }
  }
  start();
})();
