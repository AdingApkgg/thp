# TH14 current Sakuya B Hard six-stage replay · 2026-11-13

One current actual C++ Application run completes all six stages, reaches the native-style forced replay-end menu and retires its workers, timers, devices and process clock. It uses the existing intact 110,306-byte recording (`866bf6bac02e…`) and existing game assets/Vorbis. No new asset copy or original OS game run is made. Audio output is silent; graphics commands and fences are declared services, not actual GPU acceptance. The run takes 2,054.69 seconds.

The component is rebuilt against current sources and 145 verified production providers. Its Wasm remains `9b887035…`, identical to the previously verified viewer component. The startup clock/cookie profile is explicitly reused from the Normal case; it is not matched to this Hard reference. Reference state rows are read only after the Application terminates.

## Raw result and explicit diagnostic comparison

The original reference has 122,811 Player callbacks; this run has 122,796. The first five stages have equal counts. Stage 6 has 135 original callbacks at control frame zero and 120 C++ callbacks there. The raw sequence comparison fails and remains failed. Original callbacks 93,574–93,588 are recorded as the fifteen additional zero-frame callbacks; their movement/input/timer values are not claimed absent or equal in the port.

A separate diagnostic comparison explicitly lists that mapping without changing either raw file. It still reports every remaining difference. Outside stage-6 control frames 1–30, its 28 measured gameplay fields match. Actual score, graze, point value, power, life/bomb stocks/fragments and rank match throughout the mapped comparison. Input/movement/timer differences remain in those first 30 frames. This is evidence about the measured fields, not permission to suppress differences or pad the engine with fifteen updates.

The mapped HUD display word differs on 57 callbacks, all at incoming-stage control frame zero (stages 2/3/4/5/6: 20/1/11/10/15). The actual global score word matches. ANM script seed/call and brief visual-RNG call differences remain reported. The measured transition enemy-manager count is 0–2 and player-shot count is zero; no zero-bullet or invisible-object conclusion is inferred from those counts.

The terminal pause state matches the original forced exit, selection 1, five entries and three disabled entries. The last Player sample has score units 151,106,314 in both versions. The original post-award terminal score is 154,806,314; this C++ observer did not separately capture the post-award score, so the former value must not be presented as the final result. Original StageCompletion award evidence remains separate.

This accepts completion of this replay flow and records the specified diagnostic alignment. It does not accept all raw states as identical, transition GPU presentation, final PCM, detailed bullet histories, ordinary natural clear/unlock progression, all modes or the whole game. The user's current completion standard is observable behavior rather than internal/pixel identity, but the retained differences remain available for review of visible effects.

Evidence: `th14-current-sakuyab-hard-full-nov13.json`; full local audit: `artifacts/th14/current-sakuyab-hard-full-nov13/raw-audit.json`. The replay is not rerun to obtain these diagnostic comparisons. The audit's initial assumptions that transition enemy counts must be zero and that HUD differences occurred after activation were corrected from the raw data; neither assumption is a game requirement or a reason to label the engine failed.
