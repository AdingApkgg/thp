# TH14 type0: delayed batch submission and Alpha state — 2026-11-12

The type0 transition now disables separate Alpha blending before submitting the four pending edge quads, matching the original. It also resets the material blend-cache selector to10 after the Alpha-clear strip, so a previously cached blend0 cannot retain the temporary RGB factors. Only TH14's `AnmRenderer.cpp` changes; class layouts and other titles remain unchanged.

## Original submission boundary

Original `40a6f0` draws the first four embedded VMs into its quad queue. At `40ac7f..40ac8e` it disables separate Alpha blending without flushing that queue. The next background material selection calls `475eb0`; the queued edge triangles therefore reach DrawPrimitiveUP with separate Alpha disabled. The old C++ implementation flushed those edges before disabling it. The original also writes its blend-cache byte to10 at `40ac01`; the C++ path omitted that invalidation.

Earlier type0 tests recorded final quad enqueue calls at `475f80` and treated `475eb0` as a service. Matching vertices and303-word VM states in those tests did not establish the device state when the queue was finally submitted. This investigation executes actual original `475f80` queue writes and `475eb0` flush code, recording state at the D3D DrawPrimitiveUP boundary. Graphics device methods remain declared services; this oracle does not execute a physical D3D device.

360 declared cases cover states0–3, pre-interrupt updates0/79/84, post-interrupt updates0/1/10/20/40, backbuffer formats21/22, and cold/prior blend0/prior blend7 cache contexts. Both sides explicitly perform a final caller flush after the callback, including the branches which leave work pending. The first Native fixture omitted that final caller flush and is retained as a rejected boundary comparison.

| Draw-time comparison | Parent | Corrected |
| --- | ---: | ---: |
| Failed cases /360 | 135 | 0 |
| Different words /161,406 | 8,208 | 0 |

The comparison covers9,558 submitted vertices, topology/stride, exact vertex words, RGB factors/equation, separate-Alpha enable, effective Alpha factors/equation and Alpha-test enable. Inactive Alpha factors are explicitly outside the comparison, as are full texture/depth/sampler state and GPU pixels. No batch is reordered or dropped to align observations. TH12/13/16 before/after renderer objects are byte-identical across six compiler invocations. A comment-only address correction recompiles to identical TH14 object bytes.

## Actual quiet Application/GLES check

One real C++ Application cold start navigated Replay No1, Reimu B Normal, and stopped at the first stage1 Player Present:507 host frames, one Player callback,32.22 seconds. All workers, platform/GPU resources and clock ownership retired. No new original OS game or full replay ran. The module reuses145 rehashed normal providers, with fixture access relaxed only for observation.

The strict actual frame still differs from the retained original by281,902 BGRA pixels, including3,036 Alpha bytes. SCRIPT count remains2,588 versus original2,612. The transition counter is79 versus84. The first four embedded VMs remain exact across all303 fields each; the fifth retains six differences, including age and UV. A separate actual-renderer geometry component also matches all48 coordinate words of the four quads against original geometry and the retained original post-draw caches.

After the game stops, an existing diagnostic replaces only the background's two UV fields, draws without any update, then restores them. This leaves4,460 differing pixels, still a failure. Repeat and restored frames are byte-identical to the actual frame; RNG/counters do not advance, and the Alpha bytes do not change under the UV replacement. That diagnostic is not a production repair or an accepted actual frame.

The older parent sample had9,545 Alpha differences and11,694 UV-diagnostic pixel differences, but a different loading duration (counter80 instead of79). Those two runs are not a matched whole-frame improvement metric. Six retained corner diagnostics now equal original Alpha bytes where the parent differed. The complete strict results remain above, with no FPS, Alpha or spatial exclusion.

## Remaining loading phase

Particle-only geometric localization was rejected as a complete explanation: it left8,030 parent Alpha differences outside the projected particle quads. Adding the two actual loading-word VMs to the current diagnostic covers3,027 of3,036 differing Alpha pixels and4,434 of4,460 differing pixels at sample offset0. Nine Alpha differences remain outside, and sample-offset0.5 leaves47 pixels outside. These footprint calculations use measured303 geometry fields, declared clean caches, the captured Native full camera and Python projection; they are not exact GPU coverage or a pixel-acceptance mask.

The loading words themselves retain measured age/opacity differences: script14 age84/79 and Alpha244/254; script15 age84/79 and Alpha183/220 (original/C++). The initial audit's decoded Alpha labels were each one too high; its failed source and correction receipt are preserved. Raw observations and engine code were not changed by that correction.

The source fix closes a real rendering-state order gap. Loading RNG/worker chronology, all-mode/full-replay state, camera caches, full images, final PCM, ordinary complete flows and current browser UI remain open. No fixed wait, extra random call, Native state feedback during gameplay, screenshot alteration or audible output was introduced.

The browser runtime recompiles its sole changed translation unit and relinks145 hash-verified objects from the previous clean build. All source bindings are checked. Wasm SHA256:`160f41440227fe2e1ee0d66b57d0e192f7872b86050edb1cf0177e0cc26f80e5`. Deployment is recorded separately; the serving source at qualification remains28d36fe8.

Local evidence: `artifacts/th14/first-present-alpha-localization-nov12/`, including rejected particle-only coverage, embedded quad component, `batch-state/native-v2`, baseline/candidate `checked-v2.json`, `qualified.json`, `gpu-qualified.json`, real Application receipts and browser build. Public files contain source, counts, paths and hashes; assets, raw VM/pixel arrays and binaries stay local.

[Summary](th14-type0-batch-state-nov12.json)
