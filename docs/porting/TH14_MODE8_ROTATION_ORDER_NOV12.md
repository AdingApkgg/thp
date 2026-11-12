# TH14 mode8 nonzero rotation and order — 2026-11-12

Both the current matrix producer and actual AnmRenderer mode8 branch match the original producer's world/cache matrices and dirty flags for 3,456 declared nonzero-rotation cases each: 114,048 words per route, zero differences. This extends the earlier display-space check whose rotations were explicitly zero. No game behavior changes.

The matrix covers widths 640/960/1280, resolution fields 0/1/2/4, three origins, dirty masks 4/8/12, parent absent/present, all eight encoded rotation-order values, and two local XYZ triples `(0.125,-0.375,0.625)` and `(-1.25,0.75,-0.5)`. Parent angles are `(-0.25,0.5,-0.75)`. Freeze is zero throughout this new matrix; the earlier zero-rotation/frozen checks retain their separate scope. Synthetic sprite/cache matrices include off-diagonal and translation terms. Orders 6/7 exercise the original out-of-range branch, rather than being relabeled as valid Euler permutations.

Original `477c64..4780a8`, `4781af..4781de`, the actual origin producers and parent/origin helper execute. Rotation X/Y/Z and matrix multiplication are declared services supplied by the pinned real Windows x86 D3DX9_43 worker: 15,552 RPC calls, observed multiply dispatch RVA `1ba245`, worker exited 0. The cookie return is an instruction hook; original code bytes are not replaced. Import slots are redirected to the declared service boundary. The worker's FPU environment is declared; the original game's FPU environment is not inherited or accepted by this test.

The C++ component links all 141 retained normal current game providers without relaxed access, including real AnmProjection, AnmRenderer and GraphicsMath. It uses the explicitly documented comment-only header rebinding from the camera-role correction. The observation graphics boundary records the produced world matrix; it does not qualify material state, submitted geometry, GPU pixels or physical scheduling. Changing X angle rejects the reference through both routes; changing order matches its own original case and rejects the previous order.

The old direct D3DX matrix/rotation service comparison is not rerun. The new work tests their composition through the original mode8 branches with nonzero angles and encoded orders. Native VM/sprite inputs are synthetic, not captured gameplay state supplied to a running game. No original game, replay, browser or GPU run occurs, and no audio device is opened.

The current startup SCRIPT offset, whole-camera/image failures, all-mode/full-replay, complete ordinary play/save, current browser UI/persistence and final PCM remain open. Serving game source `572751a8…` and Wasm `9b17c2e2…` are unchanged. This proof does not increment complete-game acceptance.

[Summary](th14-mode8-rotation-order-nov12.json). Local evidence: `artifacts/th14/mode8-rotation-nov12/`. Public Git contains tools and counts/paths/hashes; synthetic VM buffers, original-derived matrices, worker binaries and Wasm remain local.
