# TH14 mode8 display scale and origin — 2026-11-12

The mode8 renderer now supplies the current display scale and both original origin conventions to the matrix producer. Previously resolution mode1 omitted display scaling, mode2 used a fixed half scale, and position transformation implicitly used 640×480 origins. The default display concealed these errors.

## Implementation

`AnmProjection.cpp` adds a TH14-only render-space entry point, retaining the existing default-space API. Resolution mode1 multiplies the X/Y diagonal by display scale; mode2 first rounds `scale * .5f`, then multiplies. The same space reaches the original-compatible position helper. Local Z remains unscaled. `AnmRenderer.cpp` passes the current render dimensions into that entry point, with signed integer divisions and truncation matching the original origin producers. No VM or renderer class layout changes.

Original instructions executed for the comparison: matrix slices `477c64..4780a8` and `4781af..4781de`, including parent/origin helper `4352b0`; scalar origin producers `4468eb..44690e` and `446c72..446cb6`. The original executable SHA256 is `f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353`.

## Bounded validation

6 display sizes (480×360, 640×480, 800×600, 801×623, 960×720, 1280×960), resolution modes0–7, three origin branches, four dirty states, freeze on/off, parent on/off, and two scalar samples produce 4,608 declared input cases. All new rotation inputs are zero. The comparison checks 33 words per case (world/cache matrices and dirty flags) bitwise, with no tolerance.

| Route | Failed cases before | Failed cases after | Words checked |
| --- | ---: | ---: | ---: |
| Matrix producer | 3,520 | 0 | 152,064 |
| Actual mode8 `AnmRenderer::draw` at a recording graphics boundary | 3,520 | 0 | 152,064 |

Before the fix there were 8,480 different words per route. A first candidate swapped the two origins and failed 1,280 cases; that rejected candidate and its results are retained locally. Only the corrected candidate was adopted. These are actual original instruction comparisons on declared synthetic VM inputs, not nondefault-resolution GPU pixel acceptance. Cookie service `4854a0` is a declared return boundary; original material, texture, device and OS game execution are outside this oracle.

TH13/TH16 baseline and candidate builds of both translation units produced four byte-identical object pairs (eight compiler invocations). A fresh normal-access TH14 build compiled all141 game providers; every object matches the qualified candidate set. A separate clean browser build compiled all146 units with no reused objects. Its Wasm SHA256 is `ddc22a7aa09a8284da53d40c9db1dfca3198659e890a9a7097a75d89194d9158`.

One quiet cold actual C++ Application/GLES run entered the Reimu B Normal No1 replay through the normal menu and stopped at the first stage1 Player Present (508 host frames, one Player callback). Its76 live VM snapshots (303 words each, 92,136 bytes including header) are byte-identical to the prior default-display run. The two complete frames differ by37 pixels within `[607,470,612,477]`, the FPS text bounds. The strict whole-frame result is still a failure; the current frame differs from the retained original by197,644 pixels. All workers, timers, GPU objects and platform resources retired. This run does not establish full replay or game equivalence.

The browser interface timed out twice while connecting to its existing tab. No new tab or manual recovery request was made, and browser UI acceptance remains false. The serving runtime at qualification was still `e6b15d27768ee4da293c81c3c239e3d42880020b`; deployment is recorded separately. Loading RNG, camera cache, full-frame, audio and complete-game gates remain open. No frame padding, captured native-state feedback, integrity bypass or audible output was introduced.

## Reproduction and retained evidence

The dated `tools/th14-*-mode8-display-*nov12*` sources and `tools/th14-qualify-mode8-display-space-nov12.py` describe the oracle, independent builds and audits. Local results are under `artifacts/th14/mode8-display-space-nov12/`, including `native.json`, both checked routes, the rejected candidate, source adoption receipt, clean build receipts, and `qualified.json`. The accompanying public JSON contains counts, hashes and limitations only. Game assets, raw VM arrays, executables, Wasm and screenshots are excluded from the public source commit.
