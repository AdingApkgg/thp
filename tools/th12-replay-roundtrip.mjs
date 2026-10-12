// Does a replay the port saves survive being opened by the port's own parser?
//
//   node tools/th12-replay-roundtrip.mjs [frames]
//
// Run it from `runtimes/th12/th12_web`. The replay menu after an ending saves the completed run and immediately
// reopens the bytes to show their metadata; when that failed the page reported only "Completed replay metadata
// unavailable". The two calls are separated here so the failure names itself: game_session_record_save writes the
// bytes, replay_open parses them, replay_error explains the refusal. The same serializer runs in both places, so a
// stage run exercises the code path the menu used, and the shipped replays are opened alongside as a control.
import {readFileSync} from 'node:fs';
import {core, memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const path = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const frames = Number(process.argv[2] ?? 900);
const c = await core();
const raw = readFileSync(path);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const archive = c.archive_create();
if (c.archive_open(archive, data, raw.length, 12) !== 1) throw Error('archive_open failed');
const text = p => { const b = new Uint8Array(c.memory.buffer); let s = ''; for (let i = p; b[i]; ++i) s += String.fromCharCode(b[i]); return s; };

const host = c.resources_create();
if (c.resources_open(host, data, raw.length) !== 1) throw Error('resources_open failed');
const session = c.game_session_create(), render = c.comp_create();
if (c.game_session_begin(session, host, 1, 0, 0, 2, 0) !== 1) throw Error('begin: ' + c.game_session_error(session));
for (let f = 0; f < frames; ++f) {
  c.game_session_invincibility(session, 600);
  if (c.game_session_update(session, 1, 0, 0, 0, 0, 0) !== 1) throw Error('update at ' + f + ': ' + c.game_session_error(session));
  c.game_session_render(session, render);
}
console.log(`   played ${frames} frames of stage 1, stage now ${c.game_session_value(session, 2)}, ` +
  `score ${c.battle_value ? c.game_session_value(session, 7) : 0}`);

const capacity = 1 << 22, buffer = c.allocate(capacity);
const replay = c.replay_create();
let bad = 0;
for (const terminal of [0, 1]) {
  const size = c.game_session_record_save(session, terminal, 0, buffer, capacity);
  if (size <= 0) { console.log(`   save (terminal=${terminal}) refused: ${size}`); ++bad; continue; }
  const bytes = new Uint8Array(c.memory.buffer, buffer, size).slice();
  const magic = String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3]);
  const opened = c.replay_open(replay, buffer, size);
  const error = c.replay_error(replay);
  console.log(`   saved ${String(size).padStart(6)} B, magic "${magic}", version ${bytes[4] | (bytes[5] << 8)}  ` +
    `-> replay_open ${opened}${opened ? '' : ' (' + decode(error) + ')'}  decoded=${opened ? c.replay_size(replay) : 0} B`);
  if (!opened || magic !== 't12r') ++bad;
}

// Control: the replays the game ships must still open, so a parser loosened to accept our own files would show up.
let index = -1;
for (let i = 0, n = c.archive_count(archive); i < n; ++i) if (text(c.archive_name(archive, i)) === 'demo3.rpy') index = i;
if (index >= 0) {
  const size = c.archive_read(archive, index, buffer, capacity);
  const control = c.replay_create();
  const opened = c.replay_open(control, buffer, size);
  console.log(`   control: demo3.rpy ${size} B -> replay_open ${opened}${opened ? '' : ' (' + decode(c.replay_error(control)) + ')'}`);
  if (!opened) ++bad;
}
console.log(`   ${bad} failure(s)`);
// Exit through the code rather than process.exit: tearing the wasm instance down while the loop is still alive
// aborts with libuv's "UV_HANDLE_CLOSING" assertion, which turns a passing check into a failing exit status and
// leaves the caller waiting on the aborted child.
process.exitCode = bad ? 1 : 0;

function decode(pointer) {
  if (!pointer) return '';
  const bytes = new Uint8Array(c.memory.buffer, pointer, 256);
  let s = '';
  for (const b of bytes) { if (!b) break; s += String.fromCharCode(b); }
  return s;
}
