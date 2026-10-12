// Does the message resource the battle holds actually contain the file the harness names?
//
//   node tools/th12-message-check.mjs [stage]
//
// Run it from `runtimes/th12/th12_web`. tools/th12-dialogue-timing.mjs reported the same duration for four different
// files, which cannot be true of four different instruction streams. Rather than reason about which layer could
// substitute a file, this compares bytes: the archive entry named `st<stage>_<i/2><a|b>.msg` against the bytes the
// battle's message resource holds at index i, with sizes and a hash, so "the wrong file reached the engine" and
// "the engine reads it correctly and the durations are explained some other way" are told apart by data.
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {core, memory} from '../runtimes/th12/th12_web/tests/cpp/helpers.mjs';

const stage = Number(process.argv[2] ?? 1);
const DAT = process.env.TH12_DATA ?? 'H:/Games/th/12/th12.dat';
const c = await core();
const raw = readFileSync(DAT);
const data = c.allocate(raw.length);
memory(c, data, raw.length).set(raw);
const archive = c.archive_create();
if (c.archive_open(archive, data, raw.length, 12) !== 1) throw Error('archive_open failed');
const count = c.archive_count(archive);
const textOf = p => { const v = new Uint8Array(c.memory.buffer); let s = ''; for (let i = p; v[i]; ++i) s += String.fromCharCode(v[i]); return s; };
const names = [];
for (let i = 0; i < count; ++i) names.push(textOf(c.archive_name(archive, i)));

const source = c.resources_create();
if (c.resources_open(source, data, raw.length) !== 1) throw Error('resources_open failed');
const session = c.game_session_create(), render = c.comp_create();
if (c.game_session_begin(session, source, stage, 0, 0, 2, 0) !== 1) throw Error('begin: ' + c.game_session_error(session));

const prefix = `st${String(stage).padStart(2, '0')}`;
const hash = b => createHash('sha256').update(b).digest('hex').slice(0, 16);
let bad = 0;
for (let file = 0; file < 8; ++file) {
  const name = `${prefix}_${String(file >> 1).padStart(2, '0')}${file & 1 ? 'b' : 'a'}.msg`;
  const index = names.indexOf(name);
  const portSize = c.game_session_message_size(session, file);
  if (index < 0) { console.log(`   ${name}: not in the archive (port size ${portSize})`); continue; }
  const capacity = 1 << 22, buffer = c.allocate(capacity);
  const size = c.archive_read(archive, index, buffer, capacity);
  const archiveBytes = new Uint8Array(c.memory.buffer, buffer, size).slice();
  const pointer = c.game_session_message_data(session, file);
  const portBytes = pointer ? new Uint8Array(c.memory.buffer, pointer, portSize).slice() : new Uint8Array();
  const same = portSize === archiveBytes.length && Buffer.compare(Buffer.from(archiveBytes), Buffer.from(portBytes)) === 0;
  if (!same) ++bad;
  console.log(`   ${name}: archive ${String(archiveBytes.length).padStart(5)} B ${hash(archiveBytes)}  ` +
    `port index ${file}: ${String(portSize).padStart(5)} B ${hash(portBytes)}  ${same ? 'SAME' : 'DIFFERENT'}`);
}
console.log(`   ${bad} file(s) differ between the archive and the message resource`);
process.exit(bad ? 1 : 0);
