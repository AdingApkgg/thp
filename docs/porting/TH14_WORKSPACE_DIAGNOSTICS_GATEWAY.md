# TH14 workspace diagnostic gateway

This is a prepared local diagnostic entry point. Its [prepared receipt](th14-workspace-diagnostics-gateway-prepared-oct14.json) records 47 small handler/schema/writer assertions, not an actual HTTP, browser or GPU run. The imported current/base gateway, quiet script and local passthrough Service Worker remain frozen; this tool does not delete caches or saves.

The entry point is `tools/th14-serve-workspace-diagnostics.mjs`. It listens only on `127.0.0.1:8208`, retains the frozen Launcher127 inventory, and adds one main-page link to the descriptor's literal `/checks/<slug>/` mount. The old diagnostic route list is disabled. A single descriptor and its SHA256 pin select the experiment; there is no configurable upstream, host, port or filesystem URL selector.

For the prepared angle-shader experiment, the descriptor is `artifacts/th14/stage-angle-shader-diagnostic-oct14/workspace-descriptor.json`, SHA256 `26b31b5d2b7159bce273524e1c1e0dfe9ff2779d6444a787b55430fb5b6ce94d`. It declares 54 GET mappings and two JSON POST mappings. Its HTML is a new tools copy with one scope-text correction; the original frozen artifact HTML and diagnostic manifest remain unchanged. Portable pixels are read for comparison in that page but are not newly archived.

The read-only check command is:

```powershell
C:/nvm4w/nodejs/node.exe tools/th14-serve-workspace-diagnostics.mjs --report th14-launcher-preview-prepared-staged-capture-state-oct14.json --descriptor artifacts/th14/stage-angle-shader-diagnostic-oct14/workspace-descriptor.json --descriptor-sha256 26b31b5d2b7159bce273524e1c1e0dfe9ff2779d6444a787b55430fb5b6ce94d --check
```

Omitting `--check` starts the listener; this preparation did not do so. ROOT controls the existing 8208 listener and will perform the actual browser run. The browser's current `localhost:8208` origin can remain unchanged when that server is switched. The main-page link opens `/checks/stage-angle-shaders/`; Color/UV selection uses the visible page control. Diagnostic query strings are rejected.

The exact version 1 descriptor schema is:

```json
{
  "version": 1,
  "slug": "literal-slug",
  "artifactRoot": "artifacts/th14/experiment",
  "get": [
    {"name": "", "path": "tools/experiment.html", "bytes": 123, "sha256": "64 lowercase hex characters"},
    {"name": "gpu.wasm", "path": "artifacts/th14/experiment/gpu.wasm", "bytes": 456, "sha256": "64 lowercase hex characters"}
  ],
  "post": [
    {"name": "capture/color/report.json", "basename": "color-report.json", "kind": "json", "maxBytes": 2000000, "jsonEquals": {"mode": "color", "frames": 21}},
    {"name": "capture/frame.pixels", "basename": "frame.pixels", "kind": "bytes", "bytes": 4915200}
  ]
}
```

`get` contains 1–64 exact routes and exactly one root HTML file under `tools/`; other inputs must be under `artifacts/th14/` and use an allowed runtime/data extension. Every item requires exact byte count and SHA256. `post` contains 1–16 exact request names, each mapped to a unique flat output basename. JSON is bounded at 2,000,000 bytes and can require declared scalar field values. Binary data requires an exact byte count up to 64 MiB and can additionally require `sha256`. All fields are schema-checked; extra fields, encoded paths, traversal, Windows device names and redirected paths are rejected.

The descriptor itself is hash-checked on each request. GET checks the requested input bytes; POST also rechecks the complete diagnostic input inventory. Output is confined to `artifactRoot/capture`. The writer uses exclusive create (`wx`); an existing normal file is accepted only if its size and SHA256 equal the retry payload. Different bytes are rejected without replacing the earlier evidence.

The preparation used a recording POST writer and an in-memory `wx`/`EEXIST` model. It wrote no capture output. The initial quiet-path parser unit failure and initial tool bytes are retained under `artifacts/th14/workspace-diagnostics-gateway-oct14/`; the corrected entry accepts the existing `__workspace` quiet route. None of these checks establishes shader results, physical storage writes, Native equivalence or whole-game 1:1.
