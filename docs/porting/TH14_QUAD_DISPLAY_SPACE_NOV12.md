# TH14 quad display space and pixel-coordinate broadcast — 2026-11-12

TH14 normal sprite modes0–3 and the ASCII sprite submit path now pass the current display scale and both original origin conventions into their existing geometry helpers. This completes two additional caller connections after the mode8 correction. The shared pixel submit path also follows the original four-coordinate rounding and broadcast: rounded X0/X1 become the left/right coordinates of both rows, and rounded Y0/Y2 become the top/bottom coordinates of both columns. Z remains per vertex. The previous independent per-vertex rounding differed for rotated inputs.

Only `AnmRenderer.cpp` changes in the engine, under `PORT_TITLE == 14`. VM and renderer layouts are unchanged. TH12, TH13 and TH16 each compile to a byte-identical before/after renderer object (six actual compiler invocations). The protected `ResourceCrypt.cpp` is unchanged.

## Original instruction comparisons

Actual original flat/rotated draw helpers `476100` / `4766e0`, query helper `479560`, and submit slice `4756e0..47589b` execute in private Unicorn. Submission includes original x87 rounding and the stores into the VM quad cache. Cookie return service is declared. Device/material/GPU and the complete original ASCII text wrapper are not executed.

There are two declared input sets, each6,912 cases, across six display sizes (480×360, 640×480, 800×600, 801×623, 960×720, 1280×960), resolution modes0–7, three origin branches, three anchor pairs, parent on/off, two scalar samples and draw modes0–3. One set has zero rotations. The other uses local Z rotations0.375/-0.625 and parent Z rotations-0.25/0.75. Manager offset is declared zero. The ordinary C++ renderer and ASCII query-plus-submit route each compare13,824 cases /165,888 coordinate words bitwise; both have zero differences.

The parent fails5,280 ordinary-draw cases in each set. Its ASCII route fails5,280 zero-rotation cases and5,688 nonzero-rotation cases. At640×480 its ordinary draw already matches; its nonzero ASCII control has288 failures, exposing the independent pixel-broadcast issue. These declared ASCII controls include modes beyond ordinary text's mode0 and are component coverage, not an observed original text-flow failure.

Earlier comparisons mistakenly compared post-submit rounded caches to pre-submit geometry, and subsequently used the draw-mode3 geometry for the query-mode3 route. Both rejected comparison versions and their sources/results remain preserved. Actual original submission and actual query execution establish the final comparison boundaries; no failing coordinate, mode, display size or pixel is excluded. A first corrected-source link failed because the inherited temporary directory was unwritable. That failure is preserved; a fresh output directory with explicit private TEMP/TMP linked successfully.

The independent provider set has140 unchanged game objects rehashed plus one freshly compiled renderer object, all with normal access control. The browser build likewise recompiles the sole changed unit and relinks145 hash-verified objects from the preceding clean146-unit build. All367 source bindings are checked and only the renderer input differs. No clean rebuild is claimed for this incremental build. The browser Wasm SHA256 is `38eb39b54b0b1baca465d6ee0018fa390c930f91989bb10112d5b44d3cda3ec1`.

No original OS game, actual Application or GPU session was started for this change; no new replay ran and no audible output occurred. This does not close loading RNG, camera-cache, whole-frame, nondefault-resolution GPU, browser UI, full replay/mode, audio or complete-game gates. At qualification the public runtime still used source33155d33; deployment is recorded separately. The previously captured first-Present failures remain failures.

## Evidence and reproduction

Local evidence: `artifacts/th14/quad-display-space-nov12/`, with declared inputs, draw/query/submit outputs, `baseline-submit-query`, `candidate-v3-submit-query`, their `rotations/` counterparts, other-title object checks, `qualified.json`, and `browser/build.json`. The original executable hash is `f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353`.

The dated quad-display tools cover native geometry/query/submit generation, baseline/candidate normal-provider links, checking, shared-title qualification/adoption and incremental browser construction. They require the retained previous current-core / clean browser build and original game files; start with the parent source. Failed fixture boundaries, old sources and the failed-link directory remain local. Public records contain code, counts and hashes, not assets, VM arrays, binaries or screenshots.

[Summary](th14-quad-display-space-nov12.json)

## Deployment

The corrected game source `28d36fe8f5a75988f22e8f02bcdfc06ef9492493` now serves generation `d7d2156837804bebbae1f2cc47026e4c4a91ec61e9f718b743904bf1274b4a4d` at https://wth.saop.cc/. All39 origin Runtime files match the manifest. Public HTTPS bodies for the new Wasm, loader, shell, manifest and immutable HTML match their hashes and retain COOP/COEP/no-transform. Other unchanged public bodies were not downloaded again; their prior full public check belongs to the preceding generation. Rollback is retained. Browser UI and original-game fidelity remain separately unaccepted.

[Release receipt](th14-quad-display-release-nov12.json)
