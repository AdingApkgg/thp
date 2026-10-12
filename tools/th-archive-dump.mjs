// Dump entries out of a title's archive through the port's own decoder.
//
// Used where the pinned thtk has no version number for the title (it stops at 17), so the portable reader is the
// decoder of record. Entries are matched by name suffix and only the matches are written.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { WASI } from 'node:wasi';

const here = dirname(fileURLToPath(import.meta.url));
// `here` is the tools directory, so the repository is one level up: two levels up resolved to the parent of the
// checkout and the tool reported a missing runtimes/th12/target.json outside the repo.
const repo = resolve(here, '..');
const [title, version, suffix, outDirArg] = process.argv.slice(2);
if (!title || !version) {
  console.error('usage: dump-ecl.mjs <title> <pbg-version> [suffix] [outDir]');
  process.exit(2);
}
const CORE = resolve(repo, 'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm');
const target = JSON.parse(readFileSync(resolve(repo, `runtimes/th${title}/target.json`), 'utf8'));
const archivePath = process.env.TH_DAT ?? target.dataArchives[`th${title}.dat`].path;
const outDir = resolve(outDirArg ?? resolve(repo, `runtimes/th${title}/th${title}_web/artifacts/cpp/th${title}-data`));
mkdirSync(outDir, { recursive: true });

const bytes = readFileSync(CORE);
const wasi = new WASI({ version: 'preview1', args: [], env: {}, preopens: {} });
const { instance } = await WebAssembly.instantiate(bytes, { wasi_snapshot_preview1: wasi.wasiImport });
wasi.initialize(instance);
const c = instance.exports;

const data = readFileSync(archivePath);
const p = c.allocate(data.length);
new Uint8Array(c.memory.buffer, p, data.length).set(data);
const archive = c.archive_create();
if (c.archive_open(archive, p, data.length, Number(version)) !== 1) {
  console.error(`archive_open failed for th${title}.dat as version ${version}`);
  process.exit(1);
}

const count = c.archive_count(archive);
let written = 0;
let matched = 0;
for (let n = 0; n < count; n++) {
  const ptr = c.archive_name(archive, n);
  const view = new Uint8Array(c.memory.buffer, ptr, 128);
  const end = view.indexOf(0);
  const name = new TextDecoder().decode(view.subarray(0, end < 0 ? 128 : end));
  if (suffix && !name.endsWith(suffix)) continue;
  matched++;
  const cap = c.archive_field(archive, n, 1);
  const out = c.allocate(cap);
  try {
    const size = c.archive_read(archive, n, out, cap);
    if (size !== cap) { console.error(`${name}: decoded ${size} of ${cap}`); continue; }
    writeFileSync(resolve(outDir, name), Buffer.from(new Uint8Array(c.memory.buffer, out, size)));
    written++;
  } finally {
    c.release(out);
  }
}
c.archive_delete(archive);
c.release(p);
console.log(JSON.stringify({ title: `th${title}`, archivePath, version: Number(version), entries: count, matched, written, outDir }, null, 2));
