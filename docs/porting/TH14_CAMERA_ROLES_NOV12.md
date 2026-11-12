# TH14 camera role and alignment correction — 2026-11-12

The previous shared-right publication explanation used the wrong native camera address. The code's C++ world-camera mapping was already correct; changing layer3 to another camera would introduce an error. The native roles now come from the actual `4465e0` reset's four `446250` arguments, mode/viewport fields, and independent Stage copy/draw instructions.

| C++ role | Native address | Native mode | Viewport at 640×480 |
| --- | --- | ---: | --- |
| full_camera | 0x4d93e8 | 2 | 0,0,640,480 |
| play_camera | 0x4d9190 | 0 | 32,16,384,448 |
| scaled_play_camera | 0x4d92bc | 1 | 128,16,384,448 |
| world_camera | 0x4d9514 | 3 | 116,4,408,472 |

Stage copy `40d43a` reads `0x4d9514`; Stage background `40e35e/40e365` publishes/passes the same camera before `446400`. Layer3 wrapper `47e132` passes it to `446250`, then `47e14d` uploads its cached transforms. Thus the existing C++ layer3 `set_camera(world_camera,true)` is consistent with this path. `4461e0` itself only uploads cached matrices; it does not invoke screen math. An initial linear-disassembly scan stopped on undecodable/embedded bytes and missed later calls; its empty screen-call list is not a complete call inventory.

The original world right XY pair is at `0x4d9544`, four bytes off an eight-byte boundary. It fits within the host's measured 64-byte cache line. The atomicity condition is P6-or-newer **cached** unaligned 16/32/64-bit access contained in one cache line, as specified in [Intel SDM section 7.1.1](https://www.intel.com/content/dam/support/us/en/documents/processors/pentium4/sb/25366821.pdf). The image's `.data` section is not marked noncached. Historical live page protections were not measured, so ordinary cached mapping remains an explicit condition. The previous claim that the native world pair was naturally aligned is rejected. Hardware atomicity is not inferred from Unicorn's instruction-write hook.

The C++ owner still requires eight-byte alignment for its Wasm atomic store, because misaligned Wasm atomics trap. Only the misleading C++ comment changes; layout, tokens and source line count do not. Recompiled SDK/browser SceneCompositor objects are byte-identical to the existing providers. Other providers are not rerun or silently relabeled as freshly compiled from the corrected comment. Their actual build-source bindings remain retained, with a separate comment-only source rebinding for future local work. Serving game source `572751a8…` and Wasm `9b17c2e2…` remain unchanged; this correction does not require a runtime rebuild or deployment.

The first two role attempts asserted the wrong scaled-camera address and failed. The second recorded its reset arguments before the assertion. These failures, the earlier object-audit tool/report and the previous published explanation are retained locally; the final observation identifies all four roles. The reset's screen-matrix helper is a declared service, so this audit proves role/viewport/caller identity, not those matrix values, GPU pixels or physical interleaving. It launches no original game or GPU and makes no RNG/counter adjustments.

The current 24-call RNG difference, complete camera/image comparisons, all modes/full replay, ordinary complete play/save, browser UI/persistence and final PCM remain open. A fresh browser inventory found the new public-site tab, but Chrome still returned “Debugger unattached”; there was no game UI input or new UI acceptance, and no manual user recovery was requested.

[Summary](th14-camera-roles-nov12.json). Local evidence: `artifacts/th14/camera-roles-nov12-v3/`, with rejected attempts in `camera-roles-nov12/` and `camera-roles-nov12-v2/`.
