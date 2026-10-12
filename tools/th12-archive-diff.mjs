// Development diff: portable PBG3 entry table vs thtk's, for th12.dat.
// Usage: node tools/th12-archive-diff.mjs [datPath] [version]
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';

const ws = 'H:/code/thp';
const rt = `${ws}/runtimes/th12`;
const dat = process.argv[2] ?? 'H:/Games/th/12/th12.dat';
const version = process.argv[3] ?? '12';
const thdat = `${ws}/tools/thtk/extracted/thtk-bin-12/thdat.exe`;
const coreFile = `${rt}/th12_web/artifacts/cpp/game-core-test.wasm`;

const bytes = readFileSync(coreFile);
const wasi = new WASI({ version: 'preview1', args: [], env: {}, preopens: {} });
const { instance } = await WebAssembly.instantiate(bytes, { wasi_snapshot_preview1: wasi.wasiImport });
wasi.initialize(instance);
const c = instance.exports;

const data = readFileSync(dat);
const p = c.allocate(data.length);
new Uint8Array(c.memory.buffer, p, data.length).set(data);
const archive = c.archive_create();
console.log('open=', c.archive_open(archive, p, data.length, Number(version)));
const count = c.archive_count(archive);
console.log('portable entries =', count);
const ours = [];
for (let n = 0; n < count; n++) {
  const ptr = c.archive_name(archive, n);
  const view = new Uint8Array(c.memory.buffer, ptr, 128);
  const end = view.indexOf(0);
  ours.push({
    name: new TextDecoder().decode(view.subarray(0, end < 0 ? 128 : end)),
    size: c.archive_field(archive, n, 1),
    compressed: c.archive_field(archive, n, 2),
    offset: c.archive_field(archive, n, 0),
  });
}
c.archive_delete(archive);
c.release(p);

const raw = execFileSync(thdat, ['-l', version, dat], { encoding: 'utf8' });
const theirs = [];
for (const line of raw.split(/\r?\n/)) {
  const m = /^(\S+)\s+(\d+)\s+(\d+)\s*$/.exec(line.trimEnd());
  if (m) theirs.push({ name: m[1], size: Number(m[2]), compressed: Number(m[3]) });
}
console.log('thtk entries =', theirs.length);

const ourNames = new Set(ours.map(e => e.name));
const theirNames = new Set(theirs.map(e => e.name));
const onlyOurs = ours.filter(e => !theirNames.has(e.name));
const onlyTheirs = theirs.filter(e => !ourNames.has(e.name));
console.log('only in portable:', onlyOurs.map(e => `${e.name}(${e.size})`).join(', ') || '(none)');
console.log('only in thtk    :', onlyTheirs.map(e => `${e.name}(${e.size})`).join(', ') || '(none)');

let orderMismatch = 0, fieldMismatch = 0;
for (let i = 0; i < Math.min(ours.length, theirs.length); i++) {
  if (ours[i].name !== theirs[i].name) orderMismatch++;
  if (ours[i].size !== theirs[i].size || ours[i].compressed !== theirs[i].compressed) {
    if (fieldMismatch < 10) console.log('field mismatch', i, JSON.stringify(ours[i]), JSON.stringify(theirs[i]));
    fieldMismatch++;
  }
}
console.log('order mismatches =', orderMismatch, ' field mismatches =', fieldMismatch);
console.log('last portable entries:', ours.slice(-4).map(e => e.name).join(', '));
console.log('last thtk entries    :', theirs.slice(-4).map(e => e.name).join(', '));
