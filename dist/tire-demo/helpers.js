(function () {
  const escape = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const money = (value) =>
    Number(value).toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
    });
  const comparisonRows = (products) => [
    ["Product", ...products.map((p) => `${p.brand} ${p.name}`)],
    ["Price / tire", ...products.map((p) => money(p.price))],
    [
      "Size / load / speed",
      ...products.map((p) => `${p.size} · ${p.load_index}${p.speed_symbol}`),
    ],
    ["Season", ...products.map((p) => p.season)],
    ["Available quantity", ...products.map((p) => p.available_quantity)],
    ["Location", ...products.map((p) => p.location_name)],
    ["Estimated lead time", ...products.map((p) => `${p.lead_days} day(s)`)],
    ["Observation age", ...products.map((p) => `${p.age_minutes} minutes`)],
    ["Illustrative comfort", ...products.map((p) => `${p.comfort}/10`)],
    ["Illustrative wet grip", ...products.map((p) => `${p.wet_grip}/10`)],
  ];
  const helpers = { escape, money, comparisonRows };
  if (typeof module !== "undefined") module.exports = helpers;
  else window.tireHelpers = helpers;
})();
