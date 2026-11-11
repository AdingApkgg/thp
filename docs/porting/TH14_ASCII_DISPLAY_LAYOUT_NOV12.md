# TH14 ASCII display-scaled layout — 2026-11-12

TH14 text now scales glyph advance, spaces, line breaks, shadow offsets and the numeric comma baseline by the current render width /640, matching the original text function. Initial request positions remain in their supplied coordinate space. Newline products are rounded in the original SSE order before addition. Only `AsciiText.cpp` changes; the earlier type0 batch correction is retained.

Original40bf20 multiplies horizontal steps at40c6ec, line steps at40c2b6, shadows at40c5fb/40c651 and the comma baseline at40c562 by displayScale4f7a6c. The old C++ path used unscaled steps. Earlier text checks used displayScale1 and therefore did not expose this defect; the separate geometry tests did not execute the text traversal.

The original text traversal is executed with six display multipliers from widths480,640,800,801,960,1280; all six fonts; four scale pairs including decimal0.7/0.3; shadow on/off; and two strings with spaces, punctuation and a newline. Both sides record glyph sprite, color, filter and exact X/Y float bits at the submission boundary. The sprite atlas is synthetic. Original sprite binding, geometry and GPU boundaries are declared services, and the C++ renderer submission is an observation service. This test does not prove real atlas binding, final geometry, pixels, other text alignments, queue/pass wrappers or complete HUD formatting.

| Layout comparison | Before | Corrected |
| --- | ---: | ---: |
| Failed cases /576 | 480 | 0 |
| Different words /71,280 | 16,560 | 0 |

All14,256 glyph submissions match. The96 default-width640 cases already passed before the change. TH12/13/16 before/after text objects are byte-identical. An initial shared-title compile exposed a missing name in a discarded non-template constexpr branch; the candidate now declares an unused scale1 outside TH14. The failed source/logs are retained, and recompiling TH14 after that correction produces the same object used by the successful layout check. A stale oracle docstring saying scale1 was corrected after the run; its executable AST is identical and the executed source is retained. Raw observations were not changed.

The browser build recompiles only the changed text unit and rehashes/reuses145 objects from the serving type0 build, including its corrected renderer. All367 source bindings match current source. Wasm SHA256:`7e68581101799cfdb6594da7df816d6a67763d55b7b5145c67eb053f79278b9d`. No new game process, Application/GPU test, full replay or browser UI acceptance was added. The retained type0 first-Present image still fails281,902 pixels /3,036 Alpha bytes with SCRIPT24 calls different; those measurements are not rerun or inherited as a pass for this source. Loading chronology, full images, camera caches, all-mode/full replay and ordinary complete game/save paths and final PCM remain open.

Local evidence: `artifacts/th14/ascii-display-layout-nov12/`. Public Git includes source and summary counts/paths/hashes; private observations, assets and binaries stay local. Run builders against their declared pre-change source/provider bindings; they reject overwritten evidence directories.

[Summary](th14-ascii-display-layout-nov12.json)

## Deployment

The corrected game source `9dd1ae4e2c9a4196c9bcd25f6cead5dddd9e6744` now serves generation `68c177851ed75ca0425d8ee77f401524c635ad27c51faedcebb59171c9097b0d` at https://wth.saop.cc/. All 39 origin Runtime files match the manifest. The five public HTTPS bodies checked are the new Wasm, loader, shell, manifest and immutable HTML; their hashes and COOP/COEP/no-transform headers match. Unchanged public bodies were not downloaded again. The earlier full public receipt is identified separately. Rollback remains available. This change adds no actual Application/GLES or browser UI run. The parent rendering evidence remains separately bounded; browser UI and whole-game fidelity remain unaccepted.

[Release receipt](th14-ascii-display-release-nov12.json)
