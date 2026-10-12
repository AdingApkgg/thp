// Time each dialogue entry in the port with no input and compare it with the MSG data's own waits.
//
//   node tools/th12-dialogue-timing.mjs [stage] [file-filter]
//
// Run it from `runtimes/th12/th12_web`. tools/th12-msg-timeline.mjs sums what the original's MSG data costs: every
// instruction whose time has not arrived and every opcode 11 wait, where a wait costs exactly its own value because
// the dialogue interpreter stops ticking its time while it waits. This runs the same entries through the port's
// dialogue engine with no input at all - no press can skip a wait - and reports the two numbers side by side, which
// is a check of the transcription rather than of an impression.
import {readFileSync} from 'node:fs';
import {core, memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const stage = Number(process.argv[2] ?? 1);
const filter = process.argv[3] ?? '';
const DAT = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const c = await core();
const raw = readFileSync(DAT);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const archive = c.archive_create();
if (c.archive_open(archive, data, raw.length, 12) !== 1) throw Error('archive_open failed');
const count = c.archive_count(archive);
const prefix = `st${String(stage).padStart(2, '0')}`;

const u16 = (b, o) => b[o] | (b[o + 1] << 8);
const u32 = (b, o) => (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0;
const i32 = (b, o) => u32(b, o) | 0;
const textOf = p => { const v = new Uint8Array(c.memory.buffer); let s = ''; for (let i = p; v[i]; ++i) s += String.fromCharCode(v[i]); return s; };

function expected(bytes, start) {
  let time = 0, total = 0, offset = start;
  while (offset + 4 <= bytes.length) {
    const at = u16(bytes, offset);
    if (at > time) { total += at - time; time = at; }
    const opcode = bytes[offset + 2], length = bytes[offset + 3];
    if (offset + 4 + length > bytes.length) break;
    if (opcode === 0) break;
    // A wait costs value - 1 frames: the original at 0x420810 sets the wait, at 0x420822 advances it by one and only
    // then tests it at 0x420833, so the setting frame is the wait's first decrement and the instruction is passed on
    // the frame the value reaches zero. See tools/th12-msg-timeline.mjs.
    if (opcode === 11) { const value = i32(bytes, offset + 4); if (value > 0) total += value - 1; }
    offset += 4 + length;
  }
  return total;
}

// The message resources are a flat list: GameResources builds st<stage>_<i/2><a|b>.msg, so index i is that name.
// Naming the index is what makes this a measurement of a chosen entry rather than of whichever entry the battle's
// enemy environment happens to point at - every stage-one file has an id 0 and an id 1, and a run that only passes
// the id gets the same file every time, which reads as a perfectly stable wrong answer.
const jobs = [];
for (let file = 0; file < 32; ++file) {
  const name = `st${String(stage).padStart(2, '0')}_${String(file >> 1).padStart(2, '0')}${file & 1 ? 'b' : 'a'}.msg`;
  if (filter && !name.includes(filter)) continue;
  let index = -1;
  for (let i = 0; i < count; ++i) if (textOf(c.archive_name(archive, i)) === name) { index = i; break; }
  if (index < 0) continue;
  const capacity = 1 << 22, buffer = c.allocate(capacity);
  const size = c.archive_read(archive, index, buffer, capacity);
  if (size < 0) continue;
  const bytes = new Uint8Array(c.memory.buffer, buffer, size).slice();
  for (let id = 0; id < u32(bytes, 0); ++id) jobs.push({file, name, id, expected: expected(bytes, u32(bytes, 4 + id * 8))});
}

const source = c.resources_create();
if (c.resources_open(source, data, raw.length) !== 1) throw Error('resources_open failed');
// A fresh session per entry: running a second dialogue inside a battle that has already played one leaves the
// dialogue machinery in a state the next entry inherits, and a leaked state would show up as a wildly short entry.
function freshSession() {
  const session = c.game_session_create(), render = c.comp_create();
  if (c.game_session_begin(session, source, stage, 0, 0, 2, 0) !== 1) throw Error('begin: ' + c.game_session_error(session));
  // The dialogue's animations come from resources the battle loads, so the stage runs briefly first.
  for (let f = 0; f < 60; ++f) {
    c.game_session_update(session, 0, 0, 0, 0, 0, 0);
    c.game_session_render(session, render);
  }
  return {session, render};
}

let bad = 0;
for (const job of jobs) {
  const {session} = freshSession();
  // Isolated: the dialogue interpreter alone, because reaching a dialogue through the battle lets the stage's script
  // close it at a frame of its own choosing and every long entry then looks the same length.
  const frames = c.game_session_dialogue_isolate(session, job.file, job.id, 60000);
  const verdict = frames === job.expected ? 'PASS' : 'DIFF';
  if (frames !== job.expected) ++bad;
  console.log(`   ${job.name} id ${job.id}: port ${String(frames).padStart(6)} frames, MSG data ${String(job.expected).padStart(6)} frames  ${verdict}`);
}
console.log(`   ${jobs.length} dialogue entries, ${bad} differing`);
process.exit(bad ? 1 : 0);
