// Does a replay produce press edges, and does the dialogue see them?
//
//   node tools/th12-replay-press.mjs [demo3.rpy] [frames]
//
// Run it from `runtimes/th12/th12_web`. Replay input is a stream of held words with a change record, so a button
// that goes from up to down should appear as a press on the frame it changes. The dialogue's confirmation test is a
// press of the shot button, and a dialogue that never sees one runs every wait to its full length, which is exactly
// the shape of the stage that took longer than its own recording.
import {readFileSync} from 'node:fs';
import {core, memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const want = process.argv[2] ?? 'demo3.rpy';
const frames = Number(process.argv[3] ?? 6000);
const c = await core();
const raw = readFileSync(path);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const archive = c.archive_create();
if (c.archive_open(archive, data, raw.length, 12) !== 1) throw Error('archive_open failed');
const host = c.resources_create();
if (c.resources_open(host, data, raw.length) !== 1) throw Error('resources_open failed');

const text = p => { const b = new Uint8Array(c.memory.buffer); let s = ''; for (let i = p; b[i]; ++i) s += String.fromCharCode(b[i]); return s; };
let index = -1;
for (let i = 0, n = c.archive_count(archive); i < n; ++i) if (text(c.archive_name(archive, i)) === want) index = i;
if (index < 0) throw Error(`${want} not in the archive`);
const capacity = 1 << 22, buffer = c.allocate(capacity);
const size = c.archive_read(archive, index, buffer, capacity);
const replayBytes = new Uint8Array(c.memory.buffer, buffer, size).slice();
const replay = c.allocate(replayBytes.length);
memory(c, replay, replayBytes.length).set(replayBytes);

const session = c.game_session_create(), render = c.comp_create();
if (c.game_session_replay(session, host, replay, replayBytes.length, 0, 1) !== 1) throw Error('replay refused');

let pressFrames = 0, shootPressFrames = 0, heldFrames = 0, dialogueFrames = 0, waitsSkipped = 0, lastHeld = 0;
for (let f = 0; f < frames; ++f) {
  if (c.game_session_update(session, 0, 0, 0, 0, 0, 0) !== 1) { console.log(`   update failed at ${f}`); break; }
  if (c.game_session_invincibility(session, 600) < 0) { console.log('   invincibility refused'); break; }
  if (c.game_session_render(session, render) !== 1) { console.log(`   render failed at ${f}`); break; }
  const held = c.game_session_input_probe(session, 0);
  const pressed = c.game_session_input_probe(session, 1);
  if (pressed) ++pressFrames;
  if (pressed & 1) ++shootPressFrames;
  if (held) ++heldFrames;
  if (c.game_session_dialogue_probe(session, 1) === 1) {
    ++dialogueFrames;
    // A press of the shot button while a wait is pending is the confirmation the dialogue consumes.
    if (pressed & 1) ++waitsSkipped;
  }
  if (f % 600 === 0 || (f < 20 && pressed)) {
    console.log(`   f=${String(f).padStart(5)} held=${held.toString(16)} pressed=${pressed.toString(16)} ` +
      `dialogue=${c.game_session_dialogue_probe(session, 1)} op=${c.game_session_dialogue_probe(session, 2)} ` +
      `stage=${c.game_session_value(session, 2)}`);
  }
  lastHeld = held;
  if (c.game_session_value(session, 2) !== 1) { console.log(`   stage left at ${f}`); break; }
}
console.log(`   ${frames} frames: ${heldFrames} with a held button, ${pressFrames} with any press, ` +
  `${shootPressFrames} with a shot press, ${dialogueFrames} with a dialogue active and ${waitsSkipped} shot presses during one`);
process.exit(0);
