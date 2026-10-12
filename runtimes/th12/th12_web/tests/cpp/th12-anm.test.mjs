// TH12 ANM differential test: the portable ANM reader vs thtk's `thanm -l`.
//
// th12's sprite archives are ANM version 7. The claim under test is that the
// portable reader reproduces, for every `.anm` inside th12.dat, the same texture
// table (name/format/width/height/priority), sprite table (source id, texture,
// rectangle) and script table (source id) that thtk reports.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

const THANM = process.env.TH12_THANM ?? resolve(root, '../tools/thtk/extracted/thtk-bin-12/thanm.exe');
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
  if (existsSync(EXTRACT) && readdirSync(EXTRACT).filter(f => f.endsWith('.anm')).length > 40) return;
  mkdirSync(EXTRACT, { recursive: true });
  execFileSync(THDAT, ['-x', String(THTK_VERSION), DAT], { cwd: EXTRACT, stdio: 'pipe' });
}

function thanmListing(file) {
  const out = execFileSync(THANM, ['-l', file], { encoding: 'utf8' });
  const model = { version: null, textures: [], sprites: [], scripts: [] };
  let current = null;
  for (const line of out.split(/\r?\n/)) {
    let m;
    if ((m = /^ENTRY #(\d+), VERSION (\d+)/.exec(line))) {
      current = { index: Number(m[1]), name: '', format: 0, width: 0, height: 0, priority: 0 };
      model.version = Number(m[2]);
      model.textures.push(current);
    } else if (current && (m = /^Name: (.*)$/.exec(line))) current.name = m[1];
    else if (current && (m = /^Format: (\d+)$/.exec(line))) current.format = Number(m[1]);
    else if (current && (m = /^Width: (\d+)$/.exec(line))) current.width = Number(m[1]);
    else if (current && (m = /^Height: (\d+)$/.exec(line))) current.height = Number(m[1]);
    else if (current && (m = /^MemoryPriority: (\d+)$/.exec(line))) current.priority = Number(m[1]);
    else if ((m = /^Sprite: (\d+) (-?[\d.]+)\*(-?[\d.]+)\+(-?[\d.]+)\+(-?[\d.]+)$/.exec(line)))
      model.sprites.push({ id: Number(m[1]), w: Number(m[2]), h: Number(m[3]), x: Number(m[4]), y: Number(m[5]) });
    else if ((m = /^Script: (-?\d+)$/.exec(line))) {
      model.scripts.push({ id: Number(m[1]), instructions: [] });
    } else if ((m = /^Instruction #(\d+): (-?\d+) (\d+) (\d+)/.exec(line)) && model.scripts.length) {
      model.scripts[model.scripts.length - 1].instructions.push({
        index: Number(m[1]), time: Number(m[2]), paramMask: Number(m[3]), type: Number(m[4]),
      });
    }
  }
  return model;
}

/** Decode a TH12 ANM v7 script from the portable reader's raw bytes. */
function decodeScript(c, anm, k) {
  const ptr = c.anm_script_bytes(anm, k);
  const size = c.anm_script_size(anm, k);
  const dv = new DataView(c.memory.buffer, ptr, size);
  const out = [];
  let cursor = 0;
  while (cursor + 8 <= size) {
    const type = dv.getUint16(cursor, true);
    const length = dv.getUint16(cursor + 2, true);
    const time = dv.getInt16(cursor + 4, true);
    const paramMask = dv.getUint16(cursor + 6, true);
    if (type === 0xffff && length === 0) break;
    if (length < 8 || length % 4 || cursor + length > size) return null;
    out.push({ index: out.length, time, paramMask, type, length });
    cursor += length;
  }
  return out;
}

test('TH12 portable ANM reader reproduces thanm for every th12.dat sprite archive', async () => {
  ensureExtraction();
  const c = await core();
  const anmFiles = readdirSync(EXTRACT).filter(f => f.endsWith('.anm')).sort();
  assert.ok(anmFiles.length >= 45, `expected >=45 anm files, found ${anmFiles.length}`);

  let totalTextures = 0, totalSprites = 0, totalScripts = 0, totalInstructions = 0, version7 = 0;
  const perFile = [];

  for (const file of anmFiles) {
    const bytes = readFileSync(resolve(EXTRACT, file));
    const expect = thanmListing(resolve(EXTRACT, file));
    if (expect.version === 7) version7++;

    const p = c.allocate(bytes.length);
    new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
    const anm = c.anm_create();
    try {
      assert.equal(c.anm_open(anm, p, bytes.length), 1, `${file}: anm_open failed`);
      assert.equal(c.anm_count(anm, 0), expect.textures.length, `${file}: texture count`);
      assert.equal(c.anm_count(anm, 1), expect.sprites.length, `${file}: sprite count`);
      assert.equal(c.anm_count(anm, 2), expect.scripts.length, `${file}: script count`);

      for (let t = 0; t < expect.textures.length; t++) {
        const ptr = c.anm_texture_name(anm, t);
        const view = new Uint8Array(c.memory.buffer, ptr, 256);
        const end = view.indexOf(0);
        const name = new TextDecoder().decode(view.subarray(0, end < 0 ? 256 : end));
        assert.equal(name, expect.textures[t].name, `${file}: texture ${t} name`);
        assert.equal(c.anm_texture_field(anm, t, 0), expect.textures[t].width, `${file}: texture ${t} width`);
        assert.equal(c.anm_texture_field(anm, t, 1), expect.textures[t].height, `${file}: texture ${t} height`);
        assert.equal(c.anm_texture_field(anm, t, 2), expect.textures[t].format, `${file}: texture ${t} format`);
        assert.equal(c.anm_texture_field(anm, t, 3), expect.textures[t].priority, `${file}: texture ${t} priority`);
      }

      for (let s = 0; s < expect.sprites.length; s++) {
        const ptr = c.anm_sprite(anm, s);
        const dv = new DataView(c.memory.buffer, ptr, 32);
        assert.equal(dv.getUint32(0, true), expect.sprites[s].id, `${file}: sprite ${s} source id`);
        assert.equal(dv.getFloat32(8, true), expect.sprites[s].x, `${file}: sprite ${s} x`);
        assert.equal(dv.getFloat32(12, true), expect.sprites[s].y, `${file}: sprite ${s} y`);
        assert.equal(dv.getFloat32(16, true), expect.sprites[s].w, `${file}: sprite ${s} width`);
        assert.equal(dv.getFloat32(20, true), expect.sprites[s].h, `${file}: sprite ${s} height`);
      }

      for (let k = 0; k < expect.scripts.length; k++) {
        assert.equal(c.anm_script_id(anm, k), expect.scripts[k].id, `${file}: script ${k} source id`);
        assert.ok(c.anm_script_size(anm, k) >= 8, `${file}: script ${k} decoded size`);
        const decoded = decodeScript(c, anm, k);
        assert.ok(decoded, `${file}: script ${k} bytecode framing`);
        assert.equal(decoded.length, expect.scripts[k].instructions.length, `${file}: script ${k} instruction count`);
        for (let i = 0; i < decoded.length; i++) {
          const e = expect.scripts[k].instructions[i], a = decoded[i];
          assert.equal(a.index, e.index, `${file}: script ${k} instr ${i} index`);
          assert.equal(a.time, e.time, `${file}: script ${k} instr ${i} time`);
          assert.equal(a.paramMask, e.paramMask, `${file}: script ${k} instr ${i} param mask`);
          assert.equal(a.type, e.type, `${file}: script ${k} instr ${i} opcode`);
        }
      }
    } finally {
      c.anm_delete(anm);
      c.release(p);
    }

    totalTextures += expect.textures.length;
    totalSprites += expect.sprites.length;
    totalScripts += expect.scripts.length;
    totalInstructions += expect.scripts.reduce((n, s) => n + s.instructions.length, 0);
    perFile.push({ file, version: expect.version, textures: expect.textures.length, sprites: expect.sprites.length, scripts: expect.scripts.length });
  }

  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-anm.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    coreSha256: sha(coreSnapshot),
    passed: true,
    files: anmFiles.length,
    version7Textures: version7,
    textures: totalTextures,
    sprites: totalSprites,
    scripts: totalScripts,
    instructions: totalInstructions,
    perFile,
  }, null, 2) + '\n');
});
