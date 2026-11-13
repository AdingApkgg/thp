# TH14 collaborator recorder reset · 2026-11-13

Review of website collaborator commit 43d31707 found a shadowed `practice` argument in the optional runtime patch. `ReplayRecorder::begin(..., bool practice, ...)` assigned `practice={}`, clearing its argument instead of the new `PracticeTh14` member. Stage-practice recordings lost their mode byte, and a recorder reused after practice could retain a previous setup and serialize unwanted practice metadata in an ordinary recording.

The patch correction is `this->practice={}`. The member reset and event clearing now preserve the caller's mode. The actual patched recorder, compiled before and after this correction, is exercised across six loadouts, five difficulty values and both mode values. Each case starts with stale optional setup/events to check the reset contract. The original has 30 mode failures and 60 stale-setup failures; the fix passes all 60. Applying the corrected patch produces exactly the compiled fixed source, including the updated Git postimage identity.

This is a finite native recorder regression check without assets or audio output. It does not accept the full practice UI, assisted playback, ordinary complete gameplay, original codec compatibility of custom USER blocks or the complete game. The ordinary deployed core has not adopted the collaborator practice patch; no Wasm rebuild or site feature deployment is justified solely by this fix.

The collaborator's default tools remain zero, and unchanged tools do not generate events. This preserves the intended optional scope, but wider ordinary-flow and custom replay checks remain pending before adopting the optional runtime.

Evidence is summarized in `th14-collaborator-recorder-reset-nov13.json`. Actual C++ fixture and builder: `tools/th14-check-collaborator-recorder-reset-nov13.cpp`, `tools/th14-build-collaborator-recorder-reset-nov13.py`; runner: `tools/th14-check-collaborator-recorder-reset-nov13.mjs`. The isolated overlay is produced from the collaborator patch, never applied to the live core tree.
