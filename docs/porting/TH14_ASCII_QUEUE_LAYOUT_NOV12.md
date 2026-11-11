# TH14 text queue coordinates and alignment — 2026-11-12

TH14 text now applies the original queue's display-scaled initial XYZ coordinates and pass1 origin before glyph layout. Center/right and vertical alignment remain explicit until the scaled origin has rounded. HUD score counters and award text retain that alignment instead of subtracting glyph widths in logical coordinates first. The earlier glyph spacing/shadow correction is retained.

Original40b9b0 multiplies request XYZ by4f7a6c at40ba15..40ba4b, then adds integer origins4f7a80/84 for pass1. Original40bf20 aligns from that physical origin. Lowering right/center alignment before scaling changes its float rounding. The prior576-case test entered40bf20 directly and did not execute this queue body; it did not establish this contract.

The C++ queue retains logical coordinates until draw. Device dimensions are declared stable between enqueue and drawing; a hypothetical mid-queue resolution change is outside this proof. Pass1 origins are derived from the native reset convention. Six widths480/640/800/801/960/1280, six fonts, three scale pairs (including0.7/0.3), shadows on/off, two strings, three passes and five horizontal/vertical alignment pairs produce6,480 cases,160,380 glyphs and962,280 comparison words. Sprite index, color, filter and XYZ float bits all match. Original queue40b9b0 and text traversal40bf20 execute, while atlas binding, geometry and GPU are declared services with a synthetic atlas. Pixels and actual atlas geometry are not accepted by this component.

The parent has no general alignment fields, so its baseline is explicitly limited to1,296 supported leading/top cases, not counted as passing the other5,184. It fails1,152 supported cases. At640, leading/top passes0/2 already match; pass1 lacks its origin. This is not a claim that the ordinary640 HUD was wholly broken.

Two production integrations execute original sidebar43144a..4318b6 and awards/time431140..43144a producers, grouping/time helpers, then the actual queue and text traversal. Across six widths,48 sidebar and144 awards/time cases compare4,372 glyphs /21,860 words: the parent fails160 cases and the corrected renderer-boundary layout matches all192. CRT formatting, lookup/retirement, atlas, geometry and GPU remain declared services; this does not prove every HUD state or retirement lifecycle.

TH14's style layout changes, so all141 normal game units and all146 normal browser units are compiled fresh; four host units are also compiled fresh for the Application check. The production browser build uses neither fixture macros nor a VFS. An initial shared-title compile found an unintended local-coordinate copy outside the TH14 guard; it was corrected before adoption. TH12/13/16 before/after text and HUD objects are byte-identical (six pairs), and the corrected TH14 text object is byte-identical to the one used by the successful comparisons. The failed source/logs are retained.

The first HUD oracle attempt restored original queue bytes but Unicorn still executed the previously translated service return, leaving the queue count0. That attempt is rejected. The corrected oracle explicitly invalidates translated blocks when switching boundaries and requires the actual queue count1. Later scope/unused-case cleanup retains identical observation rows. These are oracle corrections, not engine changes or accepted failed results.

## Current Application check

One quiet real Application/GLES cold start reached title, selected Quit using held masks2/0/2/0, exited normally and saved:400 host frames, zero Player callbacks,30.10 seconds. All workers, GPU objects, timers and clock ownership retired; the process exit was reaped. Its score file21,633 bytes and config92 bytes are exact to the preceding same-input C++ title-Quit capture; the decoded149,076-byte score has all eight valid record checksums and both config volumes remain0. This is a current C++ startup/Quit/save regression, not original ordinary-Quit UI, browser persistence, complete gameplay, image or final-PCM acceptance. Chrome inventory now responds, but an agent-created public-site tab still fails debugger attachment; no UI acceptance or manual recovery is claimed.

Browser Wasm SHA256:`2c4061e9aab6f876bb644974ef80d1c9c704859b8dc3286352fdc2de2a5fe04a`. Deployment is recorded separately.

## Loading RNG boundary remains open

A separate offline audit of the retained506b9da9 real Application capture finds47 unique identical literal root/age/counter keys with exact SCRIPT seed/count pairs. At age79/counter78 the RNG still matches, but C++ Control is enabled while Native still has flag4. Native enables at age84. Between the final pre-Player samples the difference is already24 calls; each side then consumes20 of its own calls before its first Player Present. Three isolated original403310 orbit checks reproduce both endpoint seeds and the24-call offset. These are arithmetic orbit checks, not an observed caller/interleaving trace.

Native/C++ particle inventories21/20 are consistent with one extra24-call particle. The actual producer and physical completion schedule are not uniquely proved or accepted. No fixed wait, extra RNG call, counter/handle correction or Native-state feedback is added. The earlier actual first-Present image still fails281,902 pixels /3,036 Alpha bytes; it is not rerun or inherited as a pass for this text source. Full loading chronology, images/camera caches, all modes/full replay, ordinary complete play/save, current browser UI/persistence and final PCM remain open.

Local evidence: `artifacts/th14/ascii-queue-layout-nov12/`, including fresh providers, rejected oracle/shared-guard attempts, comparisons, Application terminal receipt and browser build. Public Git contains source and counts/paths/hashes; assets, raw VM/pixel observations, saves and binaries stay local. Builders use declared pre-change/provider inputs and preserve existing evidence directories.

[Summary](th14-ascii-queue-layout-nov12.json) · [Loading boundary](th14-loading-enable-boundary-nov12.json)

## Deployment

Source `6e8dcbb4ce667718d9af3971080728d7a7739498` now serves generation `d9bc19bba2c1423e845dd84f5f59f90f4311d908259868966f59bd3bbb5aad52` at https://wth.saop.cc/. All367 build-source blobs on GitHub match the exact local bytes. All39 origin Runtime files match the manifest. The new Wasm, loader, shell, manifest and immutable HTML have matching public HTTPS body hashes and COOP/COEP/no-transform headers. Other unchanged public bodies were not downloaded again; the earlier full public receipt remains separately scoped. Rollback is retained. This does not add browser UI, all-mode or image acceptance.

[Release receipt](th14-ascii-queue-release-nov12.json)
