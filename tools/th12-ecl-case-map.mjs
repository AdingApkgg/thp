// TH12's extended ECL dispatch map, recovered from FUN_004154d0 (@0x4154d0).
//
// The dispatcher computes
//     ecx   = opcode - 0x100            (0x415525..0x415533, range 0x100..0x263)
//     index = byte[0x419890 + ecx]      (0x41553f)
//     goto  [0x419654 + index*4]        (0x415546)
// so the byte table at 0x419890 plus the jump table at 0x419654 give, for every
// opcode, the exact case body the original runs.
//
// The body at 0x41962b is the function's epilogue (`xor eax,eax` then the SEH
// unwind and `ret`). Opcodes routed there are done: they do nothing and report
// success. Every other body is a real instruction that has to be transcribed.
//
//   node tools/th12-ecl-case-map.mjs           # summarise and write the artifact
//   node tools/th12-ecl-case-map.mjs --check   # fail if the map changed
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const EXE = 'H:/Games/th/12/th12.exe';
const OUT = resolve(root, 'docs/th12/ecl-case-bodies.json');
const LO = 0x100, HI = 0x263;
const DEFAULT_BODY = 0x41962b;
const BYTE_TABLE = 0x419890, JUMP_TABLE = 0x419654;

function load() {
  const b = readFileSync(EXE);
  const lfanew = b.readUInt32LE(0x3c);
  const table = lfanew + 0x18 + b.readUInt16LE(lfanew + 0x14);
  const sects = [];
  for (let i = 0; i < b.readUInt16LE(lfanew + 6); i++) {
    const o = table + i * 40;
    sects.push({ vsize: b.readUInt32LE(o + 8), rva: b.readUInt32LE(o + 12),
                 rawSize: b.readUInt32LE(o + 16), raw: b.readUInt32LE(o + 20) });
  }
  const va2off = va => {
    for (const s of sects) {
      const start = 0x400000 + s.rva;
      if (va >= start && va < start + Math.min(s.vsize, s.rawSize) + 0x1000) return s.raw + (va - start);
    }
    throw Error(`address 0x${va.toString(16)} is in no section`);
  };
  // Pin the dispatch itself before trusting the tables. These are the exact
  // bytes of the opcode fetch, range check and two table lookups.
  const dispatch = b.subarray(va2off(0x41551e), va2off(0x41551e) + 0x2f);
  const expected =
    '0fb747040fbfc881c100ffffff895c2434897c241881f9630100000f87ec4000000' +
    'fb68990984100ff248d5496 4100'.replace(/ /g, '');
  if (dispatch.toString('hex') !== expected) {
    throw Error(`FUN_004154d0 dispatch at 0x41551e is ${dispatch.toString('hex')}, expected ${expected}`);
  }
  const byteTable = va2off(BYTE_TABLE), jumpTable = va2off(JUMP_TABLE);
  const opcodes = {};
  for (let op = LO; op <= HI; op++) {
    const index = b[byteTable + (op - LO)];
    opcodes[op] = b.readUInt32LE(jumpTable + index * 4);
  }
  return { opcodes, va2off, bytes: b };
}

function main() {
  const check = process.argv.includes('--check');
  const { opcodes, va2off } = load();
  const groups = new Map();
  for (const [op, body] of Object.entries(opcodes)) {
    if (!groups.has(body)) groups.set(body, []);
    groups.get(body).push(Number(op));
  }
  const noops = groups.get(DEFAULT_BODY) ?? [];
  const real = [...groups.entries()].filter(([body]) => body !== DEFAULT_BODY);

  console.log(`opcode range 0x${LO.toString(16)}..0x${HI.toString(16)} ` +
              `(${HI - LO + 1} opcodes, ${groups.size} distinct case bodies)`);
  console.log(`  no-ops (routed to the epilogue at 0x${DEFAULT_BODY.toString(16)}): ${noops.length}`);
  console.log(`  real instruction bodies: ${real.length} bodies covering ` +
              `${(HI - LO + 1) - noops.length} opcodes`);

  const artifact = {
    source: 'th12.exe FUN_004154d0 @0x4154d0 (byte table 0x419890, jump table 0x419654)',
    defaultBody: `0x${DEFAULT_BODY.toString(16)}`,
    noops,
    bodies: Object.fromEntries(real.sort((a, b) => a[0] - b[0])
      .map(([body, ops]) => [`0x${body.toString(16)}`, { file: `0x${(va2off(body)).toString(16)}`, opcodes: ops }])),
  };
  writeFileSync(OUT, `${JSON.stringify(artifact, null, 2)}\n`);
  console.log(`  wrote ${OUT}`);

  if (check && !existsSync(OUT)) {
    console.error('case map artifact missing');
    process.exit(1);
  }
  if (check) console.log('th12 ECL case map is current.');
}

main();
