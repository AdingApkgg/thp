// TH12 ECL differential test: the portable ECL reader vs thtk's `thecl -d 12 -r`.
//
// th12 uses the "SCPT" ECL container shared by th10-th17: a 36-byte header, an
// ANIM/ECLI include block, a u32 subroutine offset table, a name table, then
// per-subroutine "ECLH" blocks of 16-byte instructions. The claim under test is
// that the portable reader reproduces, for every `.ecl` in th12.dat, the same
// subroutine list (names and order) and the same per-instruction `time`/opcode
// sequence that thecl reports.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

const THECL = process.env.TH12_THECL ?? resolve(root, '../tools/thtk/extracted/thtk-bin-12/thecl.exe');
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
  if (existsSync(EXTRACT) && readdirSync(EXTRACT).filter(f => f.endsWith('.ecl')).length >= 9) return;
  mkdirSync(EXTRACT, { recursive: true });
  execFileSync(THDAT, ['-x', String(THTK_VERSION), DAT], { cwd: EXTRACT, stdio: 'pipe' });
}

function theclDump(file) {
  const out = execFileSync(THECL, ['-d', String(THTK_VERSION), '-r', file], { encoding: 'utf8' });
  const model = { animations: [], includes: [], subs: [] };
  let sub = null;
  let time = 0;
  for (const raw of out.split(/\r?\n/)) {
    const line = raw.trim();
    let m;
    if ((m = /^void (\S+?)\(\)/.exec(line))) {
      sub = { name: m[1], instructions: [] };
      model.subs.push(sub);
      time = 0;
    } else if (sub && line === '}') {
      sub = null;
    } else if ((m = /^([+-]?\d+): \/\/\s*(-?\d+)$/.exec(line))) {
      time = Number(m[2]);
    } else if (sub && (m = /^ins_(\d+)\(/.exec(line))) {
      sub.instructions.push({ time, opcode: Number(m[1]) });
    }
  }
  const anim = /anim\s*\{([^}]*)\}/.exec(out);
  if (anim) model.animations = [...anim[1].matchAll(/"([^"]*)"/g)].map(x => x[1]);
  const ecli = /ecli\s*\{([^}]*)\}/.exec(out);
  if (ecli) model.includes = [...ecli[1].matchAll(/"([^"]*)"/g)].map(x => x[1]);
  return model;
}

function readString(c, ptr) {
  const view = new Uint8Array(c.memory.buffer, ptr, 256);
  const end = view.indexOf(0);
  return new TextDecoder().decode(view.subarray(0, end < 0 ? 256 : end));
}

function ourSub(c, prog, i) {
  const ptr = c.ecl_header(prog, i);
  const size = c.ecl_size(prog, i);
  const view = new Uint8Array(c.memory.buffer, ptr, size);
  const dv = new DataView(view.buffer, view.byteOffset, size);
  const instructions = [];
  // 16-byte ECLH block header, then 16-byte instructions.
  for (let p = 16; p < size; ) {
    assert.ok(p + 16 <= size, `instruction header out of range at ${p}`);
    const time = dv.getInt32(p, true);
    const opcode = dv.getUint16(p + 4, true);
    const length = dv.getUint16(p + 6, true);
    assert.ok(length >= 16 && length % 4 === 0 && p + length <= size, `bad instruction length ${length} at ${p}`);
    instructions.push({ time, opcode });
    p += length;
  }
  return { name: readString(c, c.ecl_name(prog, i)), instructions };
}

test('TH12 portable ECL reader reproduces thecl for every th12.dat enemy script', async () => {
  ensureExtraction();
  const c = await core();
  const eclFiles = readdirSync(EXTRACT).filter(f => f.endsWith('.ecl')).sort();
  assert.ok(eclFiles.length >= 9, `expected >=9 ecl files, found ${eclFiles.length}`);

  let totalSubs = 0, totalInstructions = 0;
  const perFile = [];

  for (const file of eclFiles) {
    const bytes = readFileSync(resolve(EXTRACT, file));
    const expect = theclDump(resolve(EXTRACT, file));

    const p = c.allocate(bytes.length);
    new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
    const prog = c.ecl_create();
    try {
      assert.ok(c.ecl_attach(prog, p, bytes.length) >= 0, `${file}: ecl_attach failed`);
      assert.equal(c.ecl_count(prog, 0), 1, `${file}: file count`);
      assert.equal(c.ecl_count(prog, 1), expect.subs.length, `${file}: subroutine count`);

      const animCount = c.ecl_include_count(prog, 0, 1);
      const ecliCount = c.ecl_include_count(prog, 0, 0);
      assert.equal(animCount, expect.animations.length, `${file}: animation include count`);
      assert.equal(ecliCount, expect.includes.length, `${file}: ecl include count`);

      for (let i = 0; i < expect.subs.length; i++) {
        const ours = ourSub(c, prog, i);
        assert.equal(ours.name, expect.subs[i].name, `${file}: sub ${i} name`);
        assert.equal(ours.instructions.length, expect.subs[i].instructions.length,
          `${file}: sub ${ours.name} instruction count`);
        for (let k = 0; k < ours.instructions.length; k++) {
          assert.equal(ours.instructions[k].time, expect.subs[i].instructions[k].time,
            `${file}: ${ours.name} instr ${k} time`);
          assert.equal(ours.instructions[k].opcode, expect.subs[i].instructions[k].opcode,
            `${file}: ${ours.name} instr ${k} opcode`);
        }
        totalInstructions += ours.instructions.length;
      }
      totalSubs += expect.subs.length;
    } finally {
      c.ecl_delete(prog);
      c.release(p);
    }
    perFile.push({ file, subs: expect.subs.length, animations: expect.animations.length, includes: expect.includes.length });
  }

  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-ecl.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    coreSha256: sha(coreSnapshot),
    passed: true,
    files: eclFiles.length,
    subroutines: totalSubs,
    instructions: totalInstructions,
    perFile,
  }, null, 2) + '\n');
});
