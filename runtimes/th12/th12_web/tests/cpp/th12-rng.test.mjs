// TH12 RNG differential test: the portable C++ core vs th12.exe under the oracle.
//
// Claim under test: TH12's gameplay RNG is the same xorshift/rotl2 family the
// portable core implements, and the 8-byte state layout matches byte for byte.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { th12Oracle, TH12_RNG, writeRng, root, sha, target } from './th12-oracle.mjs';

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

const memory = (c, p, n) => new Uint8Array(c.memory.buffer, p, n);

test('TH12 RNG words and state match the original machine code', async () => {
  const c = await core();
  const m = await th12Oracle();
  const p = c.allocate(8);
  const q = m.allocate(8);
  let checks = 0;
  try {
    for (const seed of [0, 1, 0x9630, 0xffff, 0x6553, 0x8000, 12345, 54321]) {
      for (const mode of [0, 1]) {
        const b = Buffer.alloc(8);
        b.writeUInt16LE(seed);
        b.writeUInt32LE(0xfffffff0, 4);
        memory(c, p, 8).set(b);
        writeRng(m, q, seed, 0xfffffff0);

        for (let i = 0; i < 512; i++) {
          m.reg('ESI', q);
          const expected = m.call(mode === 0 ? TH12_RNG.next16 : TH12_RNG.next32, { ecx: q });
          const actual = c.rng(p, mode) >>> 0;
          assert.equal(actual, mode === 0 ? expected & 0xffff : expected >>> 0);
          assert.deepEqual(Buffer.from(memory(c, p, 8)), Buffer.from(m.bytes(q, 8)));
          checks++;
        }
      }
    }
    const dir = resolve(root, 'artifacts/cpp/verification');
    mkdirSync(dir, { recursive: true });
    writeFileSync(resolve(dir, 'th12-rng.json'), JSON.stringify({
      target: { game: target.game, version: target.version, sha256: target.sha256 },
      coreSha256: sha(coreSnapshot),
      passed: true,
      checks,
      rng: TH12_RNG,
    }, null, 2) + '\n');
  } finally {
    c.release(p);
    m.close();
  }
});

test('TH12 next32 is exactly two next16 rounds: state after 3 next32 == state after 6 next16', async () => {
  const c = await core();
  const m = await th12Oracle();
  const p = c.allocate(8);
  const q = m.allocate(8);
  try {
    for (const seed of [0, 1, 0xabcd, 0xffff, 0x1234]) {
      const b = Buffer.alloc(8);
      b.writeUInt16LE(seed);
      b.writeUInt32LE(0, 4);
      memory(c, p, 8).set(b);
      writeRng(m, q, seed, 0);

      for (let i = 0; i < 3; i++) {
        m.reg('ESI', q);
        m.call(TH12_RNG.next32, { ecx: q });
      }
      for (let i = 0; i < 6; i++) c.rng(p, 0);

      assert.deepEqual(Buffer.from(memory(c, p, 8)), Buffer.from(m.bytes(q, 8)));
    }
  } finally {
    c.release(p);
    m.close();
  }
});
