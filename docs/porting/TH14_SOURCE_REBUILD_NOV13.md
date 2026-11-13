# TH14 source rebuild and replay labels · 2026-11-13

Acceptance remains observable behavioral alignment. Normal `tools/th14-build-gles.py` builds now emit a source-derived, TH14-specialized `shell.mjs` alongside the host and native module. The normal link profile explicitly lists the seven native replay exports. Native `th11_*` C export names remain unchanged; save/data/module paths are specialized to TH14 and the archive compatibility symlink is retained.

The generated shell's executable lines match the already browser-tested shell after excluding build identity, comments and blank lines. This does not claim a new full 146-unit compile or another whole-game replay pass. The game C++ is unchanged.

The site's TH14 assembler now accepts a hash-verified shell in the core build receipt, uses it in preference to the old template, and updates its build identity. Legacy core receipts still use their verified template. An actual assembly case starts with the old pre-viewer template, verifies all 39 output identities and seven native viewer exports, and rejects a deliberately corrupted source shell. Existing optional font packaging semantics are unchanged by this edit.

The TH14 replay card previously fell back to numeric character 0 because it consulted only multiplayer loadouts. It now maps the native character/shot pair to the six existing localized Reimu, Marisa and Sakuya A/B labels without enabling multiplayer. The site's existing 45 replay-description/model/relocation tests and frontend build passed. The refreshed frontend is deployed as c7468a29. A silent actual browser check of the same persisted th14_01.rpy now displays 灵梦 B, player A, Normal and score 4370. Both volume settings remain 0%. Only this loadout was inspected in the actual browser; no claim is made that all six labels were inspected there. The game Wasm and Runtime generation remain unchanged.

Evidence: `artifacts/th14/source-delivery-nov13/source-shell-qualified.json`, `assembly-qualified.json`, and `replay-tests.log`. Tests and previews remain silent; complete-game acceptance remains open.
