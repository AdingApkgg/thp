# TH14 Purple practice browser flow · 2026-11-13

The optional website runtime at [cfb777c1](https://github.com/AdingApkgg/eagler-touhou/commit/cfb777c10324d0b56ad21fd55add4862484bb5d0) now has an actual browser check covering practice setup, custom stock, native recording and playback after a full-page reload. This is separate from the deployed normal core.

The declared base is `5eb4ac87d227027f390fa006e1126a094b820860` plus that commit's complete `launcher/patches/th14-runtime.patch`. All 153 C++/Wasm build units compile. The resulting 387 core-source and 24 common-source bindings match the actual preview worktrees. Wasm SHA-256: `2071f631a019b9552af48d4f5d63b6398775b5d1780616d9e242b67e39c5a97b`.

The frontend is built from the same website commit. Its canonical host feature configuration enables the runtime-attested TH14 practice capability and keeps the language allowlist at Japanese. Runtime capability alone does not enable the host option. The preview uses real fonts, the canonical assembler and verifier, and Btrfs copy-on-write allocation for existing game assets; installed node_modules are referenced rather than copied.

With both volume sliders at zero and music mode `none`, the actual Chrome/WebGL2 UI opens and closes F12 advanced settings, enters Practice Start through the normal title, difficulty and loadout choices, and displays the Purple parameter panel. Changing Bomb stock to six and pressing the panel's start button enters Reimu A Normal stage 1 with six Bombs. Pause and return-to-title also work.

A second custom practice run is saved through the original pause menu's save-and-exit action. Slot 1 was empty before use; the native name-entry menu saves `A`. After exiting the runtime and reloading the entire page, the file manager reads `th14_01.rpy`, identifies Reimu A / Normal / practice, and plays the entire 395-frame clip to the native replay-end menu and the frontend ended state. The observed final score 0, Power 3.50, graze 1 and six Bombs agree with the recorded run. This observation is a gameplay/UI check, not an exhaustive state comparison. No console errors or warnings were observed.

The candidate is not deployed to production. Stage/Boss warp, the mobile information panel, the other advanced tools and interoperability with a separately produced Purple replay need their own checks. The complete 395-frame recording is accepted; it is not a full stage or campaign. Whole-game completion remains false.

Private evidence: `artifacts/th14/collaborator-review-cfb777c-nov13/`; compact public evidence: [JSON](th14-purple-practice-browser-nov13.json). No game assets, fonts, binary modules, screenshots, saves or raw replay files are published with this record.
