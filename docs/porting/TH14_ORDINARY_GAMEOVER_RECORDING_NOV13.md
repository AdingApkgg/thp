# TH14 ordinary Game Over → recording → fresh playback · 2026-11-13

Acceptance follows observable game behavior, as requested, rather than internal or pixel-for-pixel 1:1 equality. This case starts a cold ordinary Reimu B Normal game using the actual C++ Application and workers. A separate replay decoder supplies held key masks only; it does not restore the source recording's position, RNG, stock, score or completion state. The session remains ordinary play throughout.

The game naturally reaches Game Over after 2,808 Player callbacks. Native menus accept the high-score name, save replay slot 01 as `A`, and return to the title. The saved file is 2,816 bytes and reports score 100,410. A fresh Application process reads a private copy of the save directory, selects the file through the native Replay menu and reaches the forced replay-end menu. It reproduces the 2,808 gameplay callbacks; natural death ends playback before the appended terminal marker is consumed.

Input, position, timers, score, graze, power, lives, bombs, gameplay RNG and HUD score observations match between ordinary play and playback. Of 32 selected fields, 29 match on every observed callback. Animation RNG differs, and one callback (2,445) reports 24 versus 22 active player shots. These differences remain recorded; this command-recording graphics fixture does not establish their visual or collision significance. This is recording and ordinary menu-flow acceptance, not full render equality or proof that every projectile matches.

The original executable's unchanged decryption and decompression routines independently read the saved file and reproduce all 17,316 decoded bytes. Allocation, copy and free are declared emulator boundaries. This checks file compatibility; the original whole game has not played this particular new file.

An initial return-to-title attempt failed because the test supplied internal held bit 256, which represents Enter at this Application boundary, while intending Escape. The corrected driver uses X (bit 2), waits for the save menu to accept input, and completes. No game-code change was necessary. The failed run and its clean retirement are retained.

Both successful processes use a silent mixer and retire owned workers, timers and devices. No reference state is fed back into gameplay. This case does not establish natural campaign completion, natural Extra unlocking, all modes, browser persistence or GPU presentation. The whole TH14 port remains in progress.

Evidence: `th14-ordinary-gameover-recording-nov13.json`. Private artifacts: `artifacts/th14/ordinary-keyscript-nov13/{save-v2,save-v3,reopen-v3,qualified.json,native-codec-qualified.json}`. Tools: `th14-build-ordinary-keyscript-nov13.py`, `th14-run-ordinary-keyscript-save-nov13.mjs`, `th14-run-ordinary-keyscript-reopen-nov13.mjs`, `th14-qualify-ordinary-keyscript-nov13.py`, and `th14-ordinary-keyscript-native-codec-nov13.py`. Game data, saves, replay bytes and binaries are not published.
