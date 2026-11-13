# TH14 current completion → ending → saved unlocks · 2026-11-13

The current C++ Application is started cold and driven through its ordinary menus as Reimu B Normal. A test-only entry invokes the same `GameBattle::dialogue_stage_complete()` method as MSG21, once each real stage and its resources are active. It does not write the stage, score, clear counters, RNG, lives, invulnerability or replay flag. This directly invokes completion boundaries and is **not a natural full campaign or natural unlock acceptance**.

The six actual stage transitions, ordinary ending `e02.msg`, staff route and Results menu complete using real C++ threads and declared graphics services. The host save writes a 21,662-byte score file. A second cold Application process reads it, returns to the normal title and reports one clear and one no-continue clear for Reimu B Normal, staff flag 1 and ending flag 0x11. Extra is available only for Reimu B. No externally unlocked score file is supplied.

The full 149,076-byte decoded score payload has eight valid record kinds, lengths and checksums. Original TH14 machine code at 4028e0/465840 independently decrypts/decompresses the same file and matches the entire independent decoded payload. CRT allocation/copy/free are declared emulator boundaries; original instructions are unchanged. This is file compatibility evidence, not original whole-game OS/UI acceptance.

Both Application processes keep audio output silent and retire owned workers, timers and devices. Their graphics boundary records commands and is not actual GPU or browser persistence acceptance. The first fixture attempt triggered stage 2 while the old battle was still in its exit delay; its failure and clean retirement remain recorded. The corrected entry waits for matching active resource and completion owners.

This verifies current completion/ending/save/reopen wiring and the tested counters/availability. Normal live gameplay, natural clear/unlock progression, all loadouts/modes, ending GPU/audio presentation and browser persistence remain separate requirements. The concurrently running Sakuya B Hard full replay does not inherit completion from this finite boundary test.

Evidence: `th14-ordinary-completion-flow-nov13.json`; private artifacts: `artifacts/th14/ordinary-completion-flow-nov13/{write-v2,read-v2,qualified.json,native-codec-qualified.json}`. Builder, v2 runner, qualifier and native-codec tool are under `tools/th14-*ordinary-completion*nov13*`. No save bytes, game assets or runtime binaries are published.
