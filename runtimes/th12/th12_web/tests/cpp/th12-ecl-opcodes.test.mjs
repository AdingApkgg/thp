// TH12 ECL opcode table validation.
//
// docs/th12/ecl-opcodes.json lists every opcode id TH12 can emit and how many
// arguments each instruction takes, extracted from thtk's `th12_fmts` table.
// thtk knows the ids but not the names, so that table is the only machine
// readable description of TH12's instruction set available without an eclmap.
//
// This test cross-validates it against the shipped bytecode: every 16-byte ECL
// instruction declares its own argument count in the header, and that count
// must equal the number of characters in the signature thtk assigns to the
// same opcode. Agreement across every instruction in every th12.dat script is
// independent evidence that both the table and our instruction framing are
// right - and it is the precondition for implementing the opcodes at all.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { WASI } from 'node:wasi';
import { root, target, sha } from './th12-oracle.mjs';

const THDAT = process.env.TH12_THDAT ?? resolve(root, '../tools/thtk/extracted/thtk-bin-12/thdat.exe');
const DAT = process.env.TH12_DAT ?? target.dataArchives['th12.dat'].path;
const EXTRACT = resolve(root, 'artifacts/cpp/th12-data');
const TABLE = resolve(root, '../../../docs/th12/ecl-opcodes.json');

const table = JSON.parse(readFileSync(TABLE, 'utf8'));
const byId = new Map(table.entries.map(e => [e.id, e]));

// thtk's grammar: each character is one argument, except that a `*` makes the
// character after it repeat for zero or more arguments (thecl10.c:1375-1389).
// Once the decoder reaches a `*` it never advances past it, so only the
// character immediately following the first `*` can repeat and anything later
// in the signature is unreachable. That gives a minimum argument count and a
// fixed-or-variadic flag.
function bounds(signature) {
  const star = signature.indexOf('*');
  return star < 0
    ? { min: signature.length, max: signature.length }
    : { min: star, max: Infinity };
}

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
  execFileSync(THDAT, ['-x', '12', DAT], { cwd: EXTRACT, stdio: 'pipe' });
}

test('TH12 ECL instructions carry exactly the argument counts thtk assigns to their opcode', async () => {
  ensureExtraction();
  const c = await core();
  const files = readdirSync(EXTRACT).filter(f => f.endsWith('.ecl')).sort();
  assert.ok(files.length >= 9, `expected >=9 ecl files, found ${files.length}`);

  const used = new Map();
  const mismatches = [];
  const unknown = [];
  let instructions = 0, subs = 0;

  for (const file of files) {
    const bytes = readFileSync(resolve(EXTRACT, file));
    const p = c.allocate(bytes.length);
    new Uint8Array(c.memory.buffer, p, bytes.length).set(bytes);
    const prog = c.ecl_create();
    try {
      assert.ok(c.ecl_attach(prog, p, bytes.length) >= 0, `${file}: ecl_attach failed`);
      const count = c.ecl_count(prog, 1);
      subs += count;
      for (let i = 0; i < count; i++) {
        const ptr = c.ecl_header(prog, i);
        const size = c.ecl_size(prog, i);
        const view = new Uint8Array(c.memory.buffer, ptr, size);
        const dv = new DataView(view.buffer, view.byteOffset, size);
        for (let at = 16; at + 16 <= size;) {
          const time = dv.getInt32(at, true);
          const id = dv.getUint16(at + 4, true);
          const length = dv.getUint16(at + 6, true);
          const declared = view[at + 11];
          if (time === -1 && id === 0xffff) break;
          assert.ok(length >= 16 && length % 4 === 0 && at + length <= size,
            `${file}: sub ${i}: bad instruction length ${length} at ${at}`);
          instructions++;
          const entry = byId.get(id);
          if (!entry) unknown.push({ file, sub: i, id });
          else {
            const { min, max } = bounds(entry.signature);
            if (declared < min || (max !== Infinity && declared !== max)) {
              mismatches.push({ file, sub: i, id, signature: entry.signature, declared, expected: max === Infinity ? `>=${min}` : String(min) });
            }
            const prev = used.get(id) ?? { id, signature: entry.signature, count: 0 };
            prev.count++;
            used.set(id, prev);
          }
          at += length;
        }
      }
    } finally {
      c.ecl_delete(prog);
      c.release(p);
    }
  }

  assert.deepEqual(unknown, [], `opcodes absent from the table: ${JSON.stringify(unknown.slice(0, 8))}`);
  assert.deepEqual(mismatches, [],
    `argument-count mismatches: ${JSON.stringify(mismatches.slice(0, 8))} (of ${mismatches.length})`);

  const usedIds = [...used.values()].sort((a, b) => a.id - b.id);
  const dir = resolve(root, 'artifacts/cpp/verification');
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, 'th12-ecl-opcodes.json'), JSON.stringify({
    target: { game: target.game, version: target.version, sha256: target.sha256 },
    table: { source: table.source, count: table.count },
    checked: { files: files.length, subroutines: subs, instructions },
    instructionCoverage: `${usedIds.length}/${table.count}`,
    usedOpcodes: usedIds,
  }, null, 2) + '\n');

  // The TH12-only half of the table (>=256) is what the TH11-derived engine
  // cannot execute today; report how much of the shipped bytecode depends on it.
  const extended = usedIds.filter(e => e.id >= 256);
  const extendedInstructions = extended.reduce((n, e) => n + e.count, 0);
  console.log(`TH12 ECL opcode table: ${instructions} instructions, ${usedIds.length}/${table.count} opcodes used, ` +
    `${extended.length} of them TH12-only (>=256) covering ${extendedInstructions} instructions`);
});
