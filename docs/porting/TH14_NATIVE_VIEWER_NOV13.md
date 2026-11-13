# TH14 hosted replay controls · 2026-11-13

Acceptance follows `TH14_BEHAVIOR_ACCEPTANCE_NOV13.md`: observable behavior, not internal or pixel identity. This change repairs the standalone replay workspace's previously unsupported playback commands. Native C++ validates replay metadata and creates the actual Application replay session. The host owns transport, timers and UI state; it does not replace recorded inputs, RNG or game state.

The viewer supports inspect/open, pause/play, bounded forward and backward seeking, six rates (0.5/1/2/4/8/full speed), byte-identical relocation, and replay after the actual end. Selected-stage offsets use native replay headers. Seeking restarts the selected native stage and advances real ticks in chunks of at most 16. The first presented native frame after a restart can be frame 1. Ordinary game cadence and native title-menu replay controls keep their existing path.

Two finite silent tests use actual C++ Application methods and physical worker threads. The 345-frame ordinary menu recording tests cold open, seek 150→30→150 with repeated measured behavior, pause/play, rate validation, relocation, end/restart and cancellation during seek. A six-stage reference tests stage-2 selection, stage-3 seeking, restart and return to stage 2. Both retire their owned timers, workers, devices and process clock. Their graphics boundary records commands; it is not actual GPU or browser acceptance.

The initial missing-namespace compile failure and early cold-loading handoff failure remain in artifacts. The fix waits for actual Application loading/worker handoff readiness. It does not inflate worker pools or insert gameplay state.

Candidate browser build recompiles one normal SDK Application unit and verifies/reuses 145 objects. It adds no runtime file: transport lives in the existing host module. Qualification is in `th14-native-viewer-nov13.json`. Actual browser workspace operation and deployment are separate pending checks; neither these tests nor previous finite replay cases establish whole-game completion. Nested replay-folder behavior is also not accepted by these flat-path cases.

Actual browser follow-up found that Chromium rejects a SharedArrayBuffer-backed view in TextDecoder. The native JSON text is now copied to an ordinary Uint8Array before decoding. The shell-command integration test enforces that browser restriction while using the actual native decoder (60 containers, one ordinary saved replay and three invalid files). The browser failure remains recorded; a passing host test does not replace the next browser retest. The Wasm binary is unchanged by this text-boundary fix.

## Actual deployed browser checks

Core `5c52c939` and a freshly rebuilt `c091d461` frontend are deployed on the TS Arch test site. All 39 complete decoded public runtime responses match their manifest and retain the required isolation headers. The browser shows the corrected “准备 TH14…” loading hint. The initial package had reused an old frontend artifact; the release preparation tool now explicitly rebuilds the UI. Existing assets and 18 Vorbis tracks are preserved with COW rollback releases.

With both volumes confirmed at 0%, the same persisted browser `th14_01.rpy` now displays player A, Normal, score 4370 and its stage-1 entry. Actual rendering reaches the native replay-end menu at 0:21 with score 4370. The progress slider Home key returns to 0:00 paused. Selecting 0.5×, playing and pausing leaves the UI at 0:10 / 0:21 with the Play button restored. These are finite actual browser checks, separately recorded in `th14-native-viewer-browser-nov13.json`.

Cross-stage controls, every rate, relocation and cancellation retain their local Application evidence; they are not all accepted as browser UI operations. The replay card still shows numeric character 0, which remains a UI gap. All-mode ordinary flows, unlock progression and remaining audio/graphics coverage remain incomplete. No whole-game completion is claimed.
