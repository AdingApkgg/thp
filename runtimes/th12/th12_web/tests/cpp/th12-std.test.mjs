// TH12 STD differential test: the portable stage-script reader vs `thstd -d 12`.
//
// The STD container holds the object ("ENTRY") directory, each object's quads,
// the per-object face instances and the background instruction stream. The claim
// under test is that the portable reader reproduces, for every `.std` in
// th12.dat, the same objects/quads/faces (including their geometry) and the same
// per-instruction `time`/opcode sequence that thstd reports.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

const THSTD = process.env.TH12_THSTD ?? resolve(root, '../tools/thtk/extracted/thtk-bin-12/thstd.exe');
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
  if (existsSync(EXTRACT) && readdirSync(EXTRACT).filter(f => f.endsWith('.std')).length >= 7) return;
  mkdirSync(EXTRACT, { recursive: true });
  execFileSync(THDAT, ['-x', String(THTK_VERSION), DAT], { cwd: EXTRACT, stdio: 'pipe' });
}

function thstdDump(file) {
  const out = execFileSync(THSTD, ['-d', String(THTK_VERSION), file], { encoding: 'utf8' });
  const model = { anm: '', objects: [], faces: [], instructions: [] };
  let object = null, quad = null, inScript = false, time = 0;
  const nums = s => [...s.matchAll(/-?\d+(?:\.\d+)?/g)].map(x => Number(x[0]));
  for (const raw of out.split(/\r?\n/)) {
    const line = raw.trim();
    let m;
    if ((m = /^ANM: (.*)$/.exec(line))) model.anm = m[1];
    else if (line === 'ENTRY:') { object = { quads: [], faces: [] }; model.objects.push(object); quad = null; }
    else if (line === 'QUAD:') { quad = {}; object.quads.push(quad); }
    else if (line === 'SCRIPT:') inScript = true;
    else if (inScript && (m = /^(\d+):$/.exec(line))) time = Number(m[1]);
    else if (inScript && (m = /^ins_(-?\d+)\(/.exec(line))) model.instructions.push({ time, opcode: Number(m[1]) });
    else if (object && (m = /^Position: (.*)$/.exec(line))) (quad ?? object).position = nums(m[1]);
    else if (object && (m = /^Unknown: (.*)$/.exec(line)) && !quad) object.unknown = nums(m[1])[0];
    else if (object && (m = /^Depth: (.*)$/.exec(line))) object.depth = nums(m[1])[0];
    else if (object && (m = /^Width: (.*)$/.exec(line))) (quad ?? object).width = nums(m[1])[0];
    else if (object && (m = /^Height: (.*)$/.exec(line))) (quad ?? object).height = nums(m[1])[0];
    else if (quad && (m = /^Type: (.*)$/.exec(line))) quad.type = nums(m[1])[0];
    else if (quad && (m = /^Script_index: (.*)$/.exec(line))) quad.scriptIndex = nums(m[1])[0];
    else if (object && (m = /^FACE: (.*)$/.exec(line))) {
      const v = nums(m[1]);
      object.faces.push({ unknown1: v[0], position: v.slice(1) });
    }
    else if (line === '}') quad = null;
  }
  return model;
}

const readString = (c, ptr) => {
  const view = new Uint8Array(c.memory.buffer, ptr, 256);
  const end = view.indexOf(0);
  return new TextDecoder().decode(view.subarray(0, end < 0 ? 256 : end));
};
const readFloats = (c, ptr, count) => {
  const dv = new DataView(c.memory.buffer, ptr, count * 4);
  return Array.from({ length: count }, (_, i) => dv.getFloat32(i * 4, true));
};

test('TH12 portable STD reader reproduces thstd for every th12.dat stage script', async () => {
  ensureExtraction();
  const c = await core();
  const stdFiles = readdirSync(EXTRACT).filter(f => f.endsWith('.std')).sort();
  assert.ok(stdFiles.length >= 7, `expected >=7 std files, found ${stdFiles.length}`);

  let objects = 0, quads = 0, faces = 0, instructions = 0;
  const perFile = [];

  for (const file of stdFiles) {
    const bytes = readFileSync(resolve(EXTRACT, file));
    const expect = thstdDump(resolve(EXTRACT, file));

    const p = c.allocate(bytes.length);
    new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
    const f = c.std_create();
    try {
      assert.equal(c.std_load(f, p, bytes.length), 1, `${file}: std_load failed`);
      assert.equal(readString(c, c.std_animation_name(f)), expect.anm, `${file}: animation name`);
      assert.equal(c.std_count(f, 0), expect.objects.length, `${file}: object count`);

      for (let i = 0; i < expect.objects.length; i++) {
        const e = expect.objects[i];
        assert.equal(c.std_count(f, 0) > i, true);
        const unknown = (c.std_object_scalar(f, i, 1) | (c.std_object_scalar(f, i, 2) << 8)) >>> 0;
        assert.equal(unknown, e.unknown, `${file}: object ${i} Unknown`);
        assert.deepEqual(readFloats(c, c.std_object_vec(f, i, 0), 3), e.position, `${file}: object ${i} position`);
        const size = readFloats(c, c.std_object_vec(f, i, 1), 3);
        assert.equal(size[0], e.width, `${file}: object ${i} width`);
        assert.equal(size[1], e.height, `${file}: object ${i} height`);
        assert.equal(size[2], e.depth, `${file}: object ${i} depth`);
        assert.equal(c.std_object_scalar(f, i, 3), e.quads.length, `${file}: object ${i} quad count`);

        for (let j = 0; j < e.quads.length; j++) {
          const q = e.quads[j];
          assert.equal(c.std_primitive_scalar(f, i, j, 0), q.type, `${file}: object ${i} quad ${j} Type`);
          assert.equal(c.std_primitive_scalar(f, i, j, 1), q.scriptIndex, `${file}: object ${i} quad ${j} Script_index`);
          assert.deepEqual(readFloats(c, c.std_primitive_vec(f, i, j, 0), 3), q.position, `${file}: object ${i} quad ${j} position`);
          const qs = readFloats(c, c.std_primitive_vec(f, i, j, 1), 2);
          assert.equal(qs[0], q.width, `${file}: object ${i} quad ${j} width`);
          assert.equal(qs[1], q.height, `${file}: object ${i} quad ${j} height`);
        }
        quads += e.quads.length;

        // thstd prints FACE lines inside the ENTRY whose index equals object_id.
        const instances = [];
        for (let k = 0; k < c.std_count(f, 1); k++) if (c.std_instance_scalar(f, k, 0) === i) instances.push(k);
        assert.equal(instances.length, e.faces.length, `${file}: object ${i} face count`);
        for (let k = 0; k < instances.length; k++) {
          assert.equal(c.std_instance_scalar(f, instances[k], 1), e.faces[k].unknown1, `${file}: object ${i} face ${k} unknown1`);
          assert.deepEqual(readFloats(c, c.std_instance_vec(f, instances[k]), 3), e.faces[k].position, `${file}: object ${i} face ${k} position`);
        }
        faces += e.faces.length;
        objects++;
      }

      // The reader terminates the instruction list with a `time=-1, opcode=-1,
      // length=-1` sentinel that thstd does not print.
      const rawCount = c.std_count(f, 3);
      const last = rawCount - 1;
      assert.equal(c.std_instruction_scalar(f, last, 1), 0xffff, `${file}: missing terminator opcode`);
      assert.equal(c.std_instruction_scalar(f, last, 0) | 0, -1, `${file}: terminator time`);
      const effective = rawCount - 1;
      assert.equal(effective, expect.instructions.length, `${file}: instruction count`);

      for (let i = 0; i < effective; i++) {
        assert.equal(c.std_instruction_scalar(f, i, 0) | 0, expect.instructions[i].time, `${file}: instr ${i} time`);
        assert.equal(c.std_instruction_scalar(f, i, 1), expect.instructions[i].opcode >>> 0, `${file}: instr ${i} opcode`);
      }
      instructions += effective;
    } finally {
      c.std_delete(f);
      c.release(p);
    }
    perFile.push({ file, anm: expect.anm, objects: expect.objects.length, quads: expect.objects.reduce((n, o) => n + o.quads.length, 0), instructions: expect.instructions.length });
  }

  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-std.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    coreSha256: sha(coreSnapshot),
    passed: true,
    files: stdFiles.length, objects, quads, faces, instructions, perFile,
  }, null, 2) + '\n');
});
