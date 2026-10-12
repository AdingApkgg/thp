// TH12 archive differential test: the portable C++ PBG3 reader vs thtk on th12.dat.
//
// Ground truth is produced by the pinned thtk v12 (`thdat -x 12`), which is part
// of this workspace's toolchain. Every entry must decode to the exact same bytes
// and the portable reader must agree on the full entry table (name/size/offset).
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

const THDAT = process.env.TH12_THDAT ?? resolve(root, '../tools/thtk/extracted/thtk-bin-12/thdat.exe');
const DAT = process.env.TH12_DAT ?? target.dataArchives['th12.dat'].path;
const EXTRACT = resolve(root, 'artifacts/cpp/th12-data');
const THTK_VERSION = 12;

let coreSnapshot;
async function core() {
  const file = process.env.TH12_CORE_TEST_FILE
    ? resolve(process.env.TH12_CORE_TEST_FILE)
    : resolve(root, 'artifacts/cpp/game-core-test.wasm');
  const bytes = coreSnapshot ??= readFileSync(file);
  const wasi = new WASI({ version: 'preview1', args: [], env: {}, preopens: {} });
  const { instance } = await WebAssembly.instantiate(bytes, { wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(instance);
  return instance.exports;
}

function ensureThtkExtraction() {
  if (existsSync(EXTRACT) && readdirSync(EXTRACT).length > 100) return;
  mkdirSync(EXTRACT, { recursive: true });
  execFileSync(THDAT, ['-x', String(THTK_VERSION), DAT], { cwd: EXTRACT, stdio: 'pipe' });
}

function thtkListing() {
  const out = execFileSync(THDAT, ['-l', String(THTK_VERSION), DAT], { encoding: 'utf8' });
  const rows = [];
  for (const line of out.split(/\r?\n/)) {
    const m = /^(\S+)\s+(\d+)\s+(\d+)\s*$/.exec(line.trimEnd());
    if (m) rows.push({ name: m[1], size: Number(m[2]), compressed: Number(m[3]) });
  }
  return rows;
}

test('TH12 portable PBG3 reader reproduces thtk entry table and every decoded entry', async () => {
  ensureThtkExtraction();
  const c = await core();
  const bytes = readFileSync(DAT);
  const listing = thtkListing();
  assert.ok(listing.length > 150, `unexpected thtk listing size ${listing.length}`);

  const p = c.allocate(bytes.length);
  new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
  const archive = c.archive_create();
  try {
    assert.equal(c.archive_open(archive, p, bytes.length, THTK_VERSION), 1, 'archive_open failed');
    assert.equal(c.archive_count(archive), listing.length, 'entry count differs from thtk');

    const decoded = [];
    let mismatchedNames = 0;
    const readName = n => {
      const ptr = c.archive_name(archive, n);
      const view = new Uint8Array(c.memory.buffer, ptr, 128);
      const end = view.indexOf(0);
      return new TextDecoder().decode(view.subarray(0, end < 0 ? 128 : end));
    };
    for (let n = 0; n < listing.length; n++) {
      const name = readName(n);
      if (name !== listing[n].name) mismatchedNames++;
      assert.equal(name, listing[n].name, `entry ${n} name`);
      assert.equal(c.archive_field(archive, n, 1), listing[n].size, `entry ${name} size`);
      assert.equal(c.archive_field(archive, n, 2), listing[n].compressed, `entry ${name} compressed size`);

      const cap = c.archive_field(archive, n, 1);
      const out = c.allocate(cap);
      try {
        const written = c.archive_read(archive, n, out, cap);
        assert.equal(written, cap, `entry ${name} decoded length`);
        const ours = createHash('sha256').update(new Uint8Array(c.memory.buffer, out, written)).digest('hex');
        decoded.push({ name, size: cap, sha256: ours });
      } finally {
        c.release(out);
      }
    }

    let compared = 0;
    for (const entry of decoded) {
      const file = resolve(EXTRACT, entry.name);
      if (!existsSync(file) || statSync(file).size !== entry.size) continue;
      const theirs = createHash('sha256').update(readFileSync(file)).digest('hex');
      assert.equal(entry.sha256, theirs, `entry ${entry.name} bytes differ from thtk`);
      compared++;
    }
    assert.ok(compared > 100, `only ${compared} entries compared against thtk output`);
    assert.equal(mismatchedNames, 0);

    const dir = resolve(root, 'artifacts/cpp/verification');
    mkdirSync(dir, { recursive: true });
    writeFileSync(resolve(dir, 'th12-archive.json'), JSON.stringify({
      target: { game: target.game, version: target.version, sha256: target.sha256 },
      coreSha256: sha(coreSnapshot),
      dataSha256: sha(bytes),
      passed: true,
      entries: decoded.length,
      comparedAgainstThtk: compared,
      thtkVersion: THTK_VERSION,
      entriesSha256: createHash('sha256').update(decoded.map(e => `${e.name}:${e.size}:${e.sha256}`).join('\n')).digest('hex'),
    }, null, 2) + '\n');
  } finally {
    c.archive_delete(archive);
    c.release(p);
  }
});
