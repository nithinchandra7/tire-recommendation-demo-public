export default [{
  files: ["dist/tire-demo/*.js", "dist/solution-labs/*.js", "scripts/*.cjs"],
  languageOptions: { ecmaVersion: 2022, sourceType: "script", globals: {
    window: "readonly", document: "readonly", fetch: "readonly", localStorage: "readonly",
    URL: "readonly", URLSearchParams: "readonly", setTimeout: "readonly", clearTimeout: "readonly",
    requestAnimationFrame: "readonly", performance: "readonly", navigator: "readonly",
    console: "readonly", Blob: "readonly", module: "readonly", require: "readonly",
    process: "readonly", __dirname: "readonly", Buffer: "readonly", AbortController: "readonly"
  }},
  rules: {"no-unused-vars": ["error", {argsIgnorePattern: "^_"}], "no-undef": "error", "eqeqeq": "error", "no-eval": "error"}
}];
