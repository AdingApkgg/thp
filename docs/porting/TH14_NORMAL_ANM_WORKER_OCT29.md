# TH14 normal ANM loading boundary — October 29

TH14 now checks the pending stage loader immediately before the ordinary ANM
registry update, in addition to Supervisor1. A worker minimum wait becomes ready
when 60 ms have elapsed since actual dispatch, even if its completion notification
is still queued in the main event loop. Generation checks still reject cancelled
or replaced work. No recorded frame number, RNG value or original pointer is used
by production scheduling.

The ordinary update entry is `47e5e0`, which walks manager list `+fe8208` and calls
VM update `46fe50`. The earlier candidate `47e590` calls layer35 **drawing** through
`47e810`. That mistaken interpretation and its failing comparison are retained.

## Finite checks

* Ten actual wait-helper checks cover dispatch delay, the exact 60 ms boundary,
  observation before queued completion delivery, stale generations, cancellation,
  duplicate dispatch, clock regression and deadline overflow.
* A declared original thread-scheduling experiment holds the main thread at
  `47e5e0` while the original worker restores Replay seeds at `456133` and completes
  the 28-word globals copy at `456135`. It removes only its own suspend increment.
  The hold lasted 70,609,500 ns. No instructions, seeds, counters, health or input
  were overwritten. The existing declared attract-bit clear remains in scope.
* That controlled 33,000-callback prefix matches all selected 32 state words,
  25 camera words, two HUD words, 653 VM rows with 303 words and registry order,
  288 combat checkpoints and 2,870 initial publications. The old loader also
  passes this particular controlled case: it establishes the boundary but does
  not distinguish the previously failing interleaving.
* In a separate retained 80,324-callback record, delivering the observed worker
  timestamp at a **proposed** normal-ANM boundary matches selected state, camera,
  HUD, 866 VM rows and 636 combat checkpoints. This uses the production loader
  poll and an explicit test-host clock input, without wrapping VM callbacks.
  Exact placement in that old original record remains an assumption. The original
  run naturally ends early in stage5; it is not an all-stage clear.
* Fresh real Application components on GLES and WebGPU each match the earlier
  2,264-frame startup/demo baseline, including seven assertions, two complete
  images, captured VM state, file state and 1,508,352 mixed PCM frames. No physical
  audio device is opened. The native component archive-worker feature is off;
  browser worker scheduling needs its own check.

The fresh browser build compiles 146 units. Its main Wasm SHA-256 is
`d0a305cbdb0e483d89d06189021efa1a9f3c5db95dfb353731ba295b428e5482`.
The quiet local browser check imports the same intact SakuyaB Hard Replay,
starts in stage5, completes the transition to6 and directly observes the final
stage's Sukuna Shinmyoumaru battle. The dispatched worker wait completes after
63 ms. This run is still playing; natural ending and a new whole run from stage1
are outside this increment's browser acceptance.

## Recompute

`th14-stage-worker-wait-build-oct29.py` and
`th14-stage-worker-wait-check-oct29.mjs` build and exercise the production wait
helper. `th14-normal-worker-observer-build-oct29.py` links the public host-clock
fixture to 141 verified production objects; no engine objects are rebuilt for
that fixture link. The two changed core translation units are compiled separately;
the public browser candidate is rebuilt in full because headers changed.

`th14-controlled-worker-boundary-evidence-oct29.py` verifies the original
instruction bytes, normal update walk, four ordered control events, bounded hold,
exact suspend-count restoration and adjacent Player timestamps. It rejects the
layer35 draw observation. `th14-compare-native-campaign.mjs` accepts this evidence
only through explicit `--normal-boundary-observation`; the independent campaign
verifier requires `--controlled-thread-observation` and a diagnostic prefix.
`--proposed-normal-boundary` separately declares the old-record timing assumption.

The original observer also gains an optional no-first-Player deadline and bounded
64/256/512-byte main-thread context reads at worker events. Debug-register updates
skip another thread only after a zero-time wait confirms termination. The earlier
`Wow64SetThreadContext` access-denied case remains retained; the new skip guard was
not exercised in the positive 512-byte case, so its old cause is not declared fixed.

Original assets, Replay bytes, raw memory, pixels, PCM and binaries stay private.
Only source, tools and hash metadata belong in the source release. New observation
cases preserve 100 GiB of free space and cap observations at 128 MiB.

## Remaining scope

Ordinary independent original/browser scheduling, ordinary cold Replay startup,
all-mode complete execution, full retail pixels/PCM and whole-game 1:1 fidelity
remain unaccepted. Existing negative records and mode totals are unchanged.
