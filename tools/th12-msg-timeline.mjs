// How long a stage's dialogue should take, summed from the original MSG data rather than from the port's run.
//
//   node tools/th12-msg-timeline.mjs [stage] [entry-filter]
//
// Run it from the repository root. Each `.msg` entry is a list of instructions and the dialogue interpreter spends
// frames on exactly two things: an instruction whose time has not arrived yet, and an opcode 11 wait. During a wait
// `Dialogue::update` returns before ticking `state.time`, so the wait's own value is the whole cost and the
// instruction times around it are unaffected. Summing those two costs gives the number of frames a dialogue needs,
// which is the number to compare with how many frames a recording of the stage lasts.
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

const text = p => { const v = new Uint8Array(c.memory.buffer); let s = ''; for (let i = p; v[i]; ++i) s += String.fromCharCode(v[i]); return s; };
const u16 = (b, o) => b[o] | (b[o + 1] << 8);
const u32 = (b, o) => (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0;
const i32 = (b, o) => u32(b, o) | 0;

// One entry's cost in frames, together with the opcodes it walks, so a surprising total can be pointed at.
function cost(bytes, start) {
  let time = 0, total = 0, waits = 0, instructions = 0, offset = start;
  const opcodes = new Map();
  while (offset + 4 <= bytes.length) {
    const at = u16(bytes, offset);
    if (at > time) { total += at - time; time = at; }
    const opcode = bytes[offset + 2], length = bytes[offset + 3];
    if (offset + 4 + length > bytes.length) break;
    opcodes.set(opcode, (opcodes.get(opcode) ?? 0) + 1);
    ++instructions;
    if (opcode === 0) break;
    if (opcode === 11) {
      // A wait costs value - 1 frames, not value: the original at 0x420810 sets the wait, at 0x420822 advances it
      // by one, and only then tests it at 0x420833, so the frame that sets a wait is also its first decrement and
      // the instruction is passed on the frame the value reaches zero.
      const value = i32(bytes, offset + 4);
      if (value > 0) { total += value - 1; ++waits; }
    }
    offset += 4 + length;
  }
  return {total, time, waits, instructions, opcodes};
}

let grand = 0, files = 0;
for (let i = 0; i < count; ++i) {
  const name = text(c.archive_name(archive, i));
  if (!name.startsWith(prefix) || !name.endsWith('.msg')) continue;
  if (filter && !name.includes(filter)) continue;
  const capacity = 1 << 22;
  const buffer = c.allocate(capacity);
  const size = c.archive_read(archive, i, buffer, capacity);
  if (size < 0) { console.log(`   ${name}: read failed`); continue; }
  const bytes = new Uint8Array(c.memory.buffer, buffer, size).slice();
  const entries = u32(bytes, 0);
  ++files;
  console.log(`   ${name}  ${size} bytes, ${entries} entries`);
  for (let id = 0; id < entries; ++id) {
    const offset = u32(bytes, 4 + id * 8);
    if (offset + 4 > bytes.length) { console.log(`      id ${id}: offset out of range`); continue; }
    const r = cost(bytes, offset);
    grand += r.total;
    const kinds = [...r.opcodes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k, v]) => `${k}x${v}`).join(' ');
    console.log(`      id ${id}: ${String(r.total).padStart(6)} frames, ${r.instructions} instructions, ${r.waits} waits, last time ${r.time}  [${kinds}]`);
  }
}
console.log(`   ${files} file(s) matching ${prefix}*.msg: ${grand} frames of dialogue in total (${(grand / 60).toFixed(1)} s at 60 Hz)`);
process.exit(0);
