// TH12 MSG differential test: the portable message-entry directory vs `thmsg -d 12`.
//
// A `.msg` file is a directory of `(stream_offset, flags)` pairs followed by the
// concatenated instruction streams. thstd-style gameplay correctness needs the
// full interpreter, but the directory itself is fully observable from thmsg's
// `entry N (FLAGS)` lines, so it can be pinned down exactly.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

const THMSG = process.env.TH12_THMSG ?? resolve(root, '../tools/thtk/extracted/thtk-bin-12/thmsg.exe');
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

function ensureExtraction() {
  if (existsSync(EXTRACT) && readdirSync(EXTRACT).filter(f => f.endsWith('.msg')).length >= 55) return;
  mkdirSync(EXTRACT, { recursive: true });
  execFileSync(THDAT, ['-x', String(THTK_VERSION), DAT], { cwd: EXTRACT, stdio: 'pipe' });
}

function thmsgDirectory(file) {
  const out = execFileSync(THMSG, ['-d', String(THTK_VERSION), file], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  const entries = [];
  for (const line of out.split(/\r?\n/)) {
    const m = /^entry (\d+) \((\d+)\)$/.exec(line.trim());
    if (m) entries.push({ id: Number(m[1]), flags: Number(m[2]) });
  }
  return entries;
}

test('TH12 portable MSG entry directory reproduces thmsg for every th12.dat message', async () => {
  ensureExtraction();
  const c = await core();
  const files = readdirSync(EXTRACT).filter(f => f.endsWith('.msg')).sort();
  assert.ok(files.length >= 55, `expected >=55 msg files, found ${files.length}`);

  let entries = 0;
  const perFile = [];
  for (const file of files) {
    const bytes = readFileSync(resolve(EXTRACT, file));
    const expect = thmsgDirectory(resolve(EXTRACT, file));
    assert.ok(expect.length > 0, `${file}: thmsg reported no entries`);

    const p = c.allocate(bytes.length);
    new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
    const f = c.dialog_create();
    try {
      c.dialog_load(f, p, bytes.length);
      assert.equal(c.dialog_entry_count(f), expect.length, `${file}: entry count`);
      let previous = -1;
      for (const e of expect) {
        const offset = c.dialog_locate(f, e.id);
        assert.notEqual(offset, -1, `${file}: entry ${e.id} did not resolve`);
        assert.ok(offset + 4 <= bytes.length, `${file}: entry ${e.id} offset out of range`);
        assert.ok(offset > previous, `${file}: entry ${e.id} offset not increasing`);
        previous = offset;
        assert.equal(c.dialog_locate_flags(f, e.id) >>> 0, e.flags, `${file}: entry ${e.id} flags`);
      }
      assert.equal(c.dialog_locate(f, expect.length), -1, `${file}: out-of-range entry accepted`);
    } finally {
      c.dialog_delete(f);
      c.release(p);
    }
    entries += expect.length;
    perFile.push({ file, entries: expect.length });
  }

  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-msg.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    coreSha256: sha(coreSnapshot),
    passed: true,
    files: files.length, entries, perFile,
  }, null, 2) + '\n');
});
