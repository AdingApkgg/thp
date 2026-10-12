// TH13 archive differential test: reuse the portable PBG reader on a different title.
//
// The reader in cpp/game/Archive.cpp is title-independent - it takes the archive's cipher generation as an
// argument - so a new title is verified by pointing the same reader at its archive rather than by writing a new
// one. Ground truth is thtk pinned to version 13, and the entry count is cross-checked against the number
// measured independently from the archive header.
//
// Paths resolve from the repository root, not from th12's runtime, so this test does not depend on living
// beside the th12 one.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { WASI } from 'node:wasi';

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '../../../../..');
const CORE = process.env.TH13_CORE_TEST_FILE
  ? resolve(process.env.TH13_CORE_TEST_FILE)
  : resolve(repo, 'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm');
const THDAT = process.env.TH13_THDAT ?? resolve(repo, 'runtimes/th12/tools/thtk/extracted/thtk-bin-12/thdat.exe');
// The archive is not copied into the repository (it is 44 MB and gitignored); the path comes from the target
// record, which is why that record is the thing the survey writes and this test reads.
const TARGET = resolve(repo, 'runtimes/th13/target.json');
const measured = existsSync(TARGET) ? JSON.parse(readFileSync(TARGET, 'utf8')) : null;
const DATA = process.env.TH13_DAT ?? measured?.dataArchives?.['th13.dat']?.path ?? 'H:/Games/th/13/th13.dat';
const EXTRACT = resolve(repo, 'runtimes/th13/th13_web/artifacts/cpp/th13-data');
const THTK_VERSION = 13;
// Measured from the archive's own decrypted header by tools/th-target-survey.py. Keeping it here means a listing
// that silently stops early cannot pass: the count has two independent sources.
const EXPECT_ENTRIES = 216;

let coreSnapshot;
async function core() {
  const bytes = coreSnapshot ??= readFileSync(CORE);
  const wasi = new WASI({ version: 'preview1', args: [], env: {}, preopens: {} });
  const { instance } = await WebAssembly.instantiate(bytes, { wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(instance);
  return instance.exports;
}

function ensureThtkExtraction() {
  if (existsSync(EXTRACT) && readdirSync(EXTRACT).length > 100) return;
  mkdirSync(EXTRACT, { recursive: true });
  execFileSync(THDAT, ['-x', String(THTK_VERSION), DATA], { cwd: EXTRACT, stdio: 'pipe' });
}

function thtkListing() {
  const out = execFileSync(THDAT, ['-l', String(THTK_VERSION), DATA], { encoding: 'utf8' });
  const rows = [];
  for (const line of out.split(/\r?\n/)) {
    const m = /^(\S+)\s+(\d+)\s+(\d+)\s*$/.exec(line.trimEnd());
    if (m) rows.push({ name: m[1], size: Number(m[2]), compressed: Number(m[3]) });
  }
  return rows;
}

const available = existsSync(CORE) && existsSync(DATA) && existsSync(THDAT);

test('TH13 archives open with the shared portable reader and every entry decodes', { skip: !available && 'core, th13.dat or thdat missing' }, async () => {
  const c = await core();
  const bytes = readFileSync(DATA);
  const listing = thtkListing();

  const archiveRecord = measured.dataArchives['th13.dat'];
  assert.equal(listing.length, EXPECT_ENTRIES, 'thtk listing length');
  assert.equal(archiveRecord.entries, EXPECT_ENTRIES, 'entry count measured from the archive header');

  const p = c.allocate(bytes.length);
  new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
  const archive = c.archive_create();
  try {
    assert.equal(c.archive_open(archive, p, bytes.length, THTK_VERSION), 1, 'archive_open failed for th13.dat');
    assert.equal(c.archive_count(archive), EXPECT_ENTRIES, 'portable reader entry count');

    const decoded = [];
    for (let n = 0; n < listing.length; n++) {
      const namePtr = c.archive_name(archive, n);
      const view = new Uint8Array(c.memory.buffer, namePtr, 128);
      const end = view.indexOf(0);
      const name = new TextDecoder().decode(view.subarray(0, end < 0 ? 128 : end));
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

    ensureThtkExtraction();
    let compared = 0;
    for (const entry of decoded) {
      const file = resolve(EXTRACT, entry.name);
      if (!existsSync(file) || statSync(file).size !== entry.size) continue;
      const theirs = createHash('sha256').update(readFileSync(file)).digest('hex');
      assert.equal(entry.sha256, theirs, `entry ${entry.name} bytes differ from thtk`);
      compared++;
    }
    assert.ok(compared > 100, `only ${compared} entries compared against thtk output`);

    const dir = resolve(repo, 'runtimes/th13/th13_web/artifacts/cpp/verification');
    mkdirSync(dir, { recursive: true });
    writeFileSync(resolve(dir, 'th13-archive.json'), JSON.stringify({
      target: { game: measured.game, version: measured.version, sha256: measured.sha256 },
      coreSha256: createHash('sha256').update(coreSnapshot).digest('hex'),
      dataSha256: createHash('sha256').update(bytes).digest('hex'),
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
