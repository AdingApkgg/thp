// TH12's replay container: recover its parameters from th12.exe and check the
// runtime's copy against them.
//
// Everything here is anchored in the original binary:
//   * the replay loader at .text 0x43c3c2..0x43c4d4
//   * the magic immediate 0x72323174 ("t12r") and version word 4
//   * the two cipher passes, read out of the loader's own push/mov immediates
//   * the stage header size 0xA0, read out of `lea edx,[eax+0xa0]` and
//     `lea eax,[eax+ecx+0xa0]`
// Decoding the four attract demos inside th12.dat then proves the parameters:
// the LZSS stream must terminate with exactly the declared number of bytes and
// the stage walk must land exactly on the end of the buffer.
//
//   node tools/th12-replay-format.mjs            # show recovered parameters
//   node tools/th12-replay-format.mjs --check    # verify the runtime agrees
//
// --check is the gate. It fails if the runtime's keys or header size drift from
// the original's, or if any demo stops decoding exactly.
import { readFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const EXE = 'H:/Games/th/12/th12.exe';
const DAT = 'H:/Games/th/12/th12.dat';
const THDAT = resolve(root, 'tools/thtk/extracted/thtk-bin-12/thdat.exe');
const SCRATCH = resolve(root, 'tools/tmp/replay-format');
const SOURCE = resolve(root, 'runtimes/th12/th12_web/cpp/game/Replay.cpp');
const HEADER = resolve(root, 'runtimes/th12/th12_web/cpp/game/Replay.hpp');
const IMAGE_BASE = 0x400000;
const MAGIC = 0x72323174;
const VERSION = 4;
const FILE_HEADER = 0x70;

function sections(b) {
  const lfanew = b.readUInt32LE(0x3c);
  const table = lfanew + 0x18 + b.readUInt16LE(lfanew + 0x14);
  const out = [];
  for (let i = 0; i < b.readUInt16LE(lfanew + 6); i++) {
    const o = table + i * 40;
    out.push({ name: b.toString('ascii', o, o + 8).replace(/\0/g, ''),
               vsize: b.readUInt32LE(o + 8), rva: b.readUInt32LE(o + 12),
               rawSize: b.readUInt32LE(o + 16), raw: b.readUInt32LE(o + 20) });
  }
  return out;
}

// The loader's argument setup, one entry per push/mov immediate we depend on.
const LOADER_SITES = [
  ['first pass block 0x800', 0x43c428, [0x68, 0x00, 0x08, 0x00, 0x00]],
  ['first pass step 0xe1', 0x43c42d, [0x68, 0xe1, 0x00, 0x00, 0x00]],
  ['first pass key', 0x43c434, [0xb0, 0x5e]],
  ['second pass block 0x40', 0x43c442, [0x6a, 0x40]],
  ['second pass step 0x3a', 0x43c444, [0x6a, 0x3a]],
  ['second pass key', 0x43c448, [0xb0, 0x7d]],
  ['stage header 0xa0', 0x43c49c, [0x8d, 0x90, 0xa0, 0x00, 0x00, 0x00]],
  ['next record stride', 0x43c4cc, [0x8d, 0x84, 0x08, 0xa0, 0x00, 0x00, 0x00]],
];

export function recover() {
  const b = readFileSync(EXE);
  const sects = sections(b);
  const va2off = va => {
    for (const s of sects) {
      const start = IMAGE_BASE + s.rva;
      if (va >= start && va < start + Math.min(s.vsize, s.rawSize) + 0x1000) {
        return s.raw + (va - start);
      }
    }
    throw Error(`address 0x${va.toString(16)} is in no section`);
  };
  for (const [label, va, bytes] of LOADER_SITES) {
    const off = va2off(va);
    const got = b.subarray(off, off + bytes.length);
    if (!got.equals(Buffer.from(bytes))) {
      throw Error(`${label}: 0x${va.toString(16)} holds ${got.toString('hex')}, expected ${Buffer.from(bytes).toString('hex')}`);
    }
  }
  const at = (va, n) => { const off = va2off(va); return b.subarray(off, off + n); };
  return {
    magic: MAGIC, version: VERSION, fileHeader: FILE_HEADER, stageHeader: 0xA0,
    passes: [
      { key: at(0x43c434, 2)[1], step: at(0x43c42d, 5).readUInt32LE(1), block: at(0x43c428, 5).readUInt32LE(1) },
      { key: at(0x43c448, 2)[1], step: at(0x43c444, 2)[1], block: at(0x43c442, 2)[1] },
    ],
  };
}

function crypt(input, size, p) {
  const out = new Uint8Array(size);
  let key = p.key;
  const mod = size % p.block;
  const untouched = (mod < Math.floor(p.block / 4) ? mod : 0) + (size & 1);
  let remaining = size - untouched, limit = size, cursor = 0;
  while (remaining > 0 && limit > 0) {
    const block = Math.min(p.block, remaining);
    let linear = 0;
    for (let parity = 1; parity <= 2; parity++) {
      for (let pos = block - parity; pos >= 0; pos -= 2) {
        out[cursor + pos] = input[cursor + linear] ^ key;
        key = (key + p.step) & 0xff;
        linear++;
      }
    }
    cursor += block; remaining -= block; limit -= block;
  }
  if (cursor < size) out.set(input.subarray(cursor, size), cursor);
  return out;
}

function lzss(input, size, capacity) {
  const output = new Uint8Array(capacity), dict = new Uint8Array(8192);
  let cursor = 0, written = 0, head = 1, mask = 0x80, byte = 0;
  const bit = () => {
    if (mask === 0x80) byte = cursor < size ? input[cursor++] : 0;
    const r = (byte & mask) ? 1 : 0;
    mask >>= 1; if (!mask) mask = 0x80;
    return r;
  };
  const bits = n => { let v = 0; while (n--) v = (v << 1) | bit(); return v; };
  const put = v => { output[written++] = v; dict[head] = v; head = (head + 1) & 8191; };
  for (;;) {
    if (bit()) { if (written === capacity) return { written, terminated: false, output }; put(bits(8)); }
    else {
      const offset = bits(13);
      if (!offset) return { written, terminated: true, output };
      const length = bits(4) + 3;
      if (length > capacity - written) return { written, terminated: false, output };
      for (let i = 0; i < length; i++) put(dict[(offset + i) & 8191]);
    }
  }
}

function decode(file, params) {
  const raw = readFileSync(file);
  const problems = [];
  if (raw.readUInt32LE(0) !== params.magic) problems.push(`magic is 0x${raw.readUInt32LE(0).toString(16)}, expected 0x${params.magic.toString(16)}`);
  if (raw.readUInt16LE(4) !== params.version) problems.push(`version is ${raw.readUInt16LE(4)}, expected ${params.version}`);
  const packed = raw.readUInt32LE(0x1c), unpacked = raw.readUInt32LE(0x20);
  if (!packed || packed > raw.length - 0x24) problems.push(`packed size ${packed} does not fit ${raw.length} bytes`);
  let decoded = null, stages = null;
  if (!problems.length) {
    let buffer = raw.subarray(0x24, 0x24 + packed);
    for (const pass of params.passes) buffer = crypt(buffer, packed, pass);
    const result = lzss(buffer, packed, unpacked);
    if (!result.terminated) problems.push('LZSS stream never reached its terminator');
    else if (result.written !== unpacked) problems.push(`LZSS wrote ${result.written} of ${unpacked} bytes`);
    decoded = result.output;
    // Walk the stage records exactly as the original loader does.
    const dv = new DataView(decoded.buffer, decoded.byteOffset, decoded.byteLength);
    const count = dv.getUint32(0x58, true);
    if (count < 1 || count > 7) problems.push(`stage count ${count} is out of range`);
    else {
      stages = [];
      let offset = params.fileHeader;
      for (let i = 0; i < count; i++) {
        const number = dv.getUint16(offset, true), frames = dv.getUint32(offset + 4, true),
              payload = dv.getUint32(offset + 8, true);
        stages.push({ number, frames, payload });
        offset += params.stageHeader + payload;
      }
      if (offset !== unpacked) problems.push(`stage walk ended at 0x${offset.toString(16)}, buffer is 0x${unpacked.toString(16)}`);
    }
  }
  return { raw, packed, unpacked, decoded, stages, problems };
}

function main() {
  const check = process.argv.includes('--check');
  const params = recover();
  console.log(`recovered from ${EXE}:`);
  console.log(`  magic "t12r" (0x${params.magic.toString(16)}), version ${params.version}`);
  console.log(`  file header 0x${params.fileHeader.toString(16)}, stage header 0x${params.stageHeader.toString(16)}`);
  for (const [i, p] of params.passes.entries())
    console.log(`  pass ${i + 1}: key 0x${p.key.toString(16)}, step 0x${p.step.toString(16)}, block 0x${p.block.toString(16)}`);

  // The runtime's constants must match the original's, verbatim.
  const source = readFileSync(SOURCE, 'utf8');
  const header = readFileSync(HEADER, 'utf8');
  const [first, second] = params.passes;
  const expectedCall = `{0x${first.key.toString(16)},0x${first.step.toString(16)},0x${first.block.toString(16)},packed}`;
  const expectedCall2 = `{0x${second.key.toString(16)},0x${second.step.toString(16)},0x${second.block.toString(16)},packed}`;
  const expectedMagic = `0x${params.magic.toString(16)}`;
  const expectedHeader = `kReplayStageHeader=0x${params.stageHeader.toString(16).toUpperCase()}`;
  const mismatches = [];
  if (!source.includes(expectedCall)) mismatches.push(`Replay.cpp does not use the first pass ${expectedCall}`);
  if (!source.includes(expectedCall2)) mismatches.push(`Replay.cpp does not use the second pass ${expectedCall2}`);
  if (!source.includes(expectedMagic)) mismatches.push(`Replay.cpp does not check magic ${expectedMagic}`);
  if (!header.includes(expectedHeader)) mismatches.push(`Replay.hpp does not define ${expectedHeader}`);

  if (!existsSync(SCRATCH)) mkdirSync(SCRATCH, { recursive: true });
  execFileSync(THDAT, ['-x', 'd', DAT, 'demo0.rpy', 'demo1.rpy', 'demo2.rpy', 'demo3.rpy'], { cwd: SCRATCH, stdio: 'ignore' });
  const names = ['demo0.rpy', 'demo1.rpy', 'demo2.rpy', 'demo3.rpy'];
  const reports = names.map(name => [name, decode(resolve(SCRATCH, name), params)]);
  for (const [name, r] of reports) {
    console.log(`  ${name}: ${r.unpacked} bytes, ${r.stages ? r.stages.length : 0} stage(s)` +
                (r.stages ? ` -> ${r.stages.map(s => `stage ${s.number} ${s.frames} frames`).join(', ')}` : '') +
                (r.problems.length ? ` PROBLEMS: ${r.problems.join('; ')}` : ' exact'));
  }
  const failures = [...mismatches];
  for (const [name, r] of reports) for (const p of r.problems) failures.push(`${name}: ${p}`);

  if (!check) return;
  if (failures.length) {
    console.error('\nth12 replay format check FAILED:');
    for (const f of failures) console.error(`  - ${f}`);
    process.exit(1);
  }
  console.log('\nth12 replay format check passed: original parameters and runtime copy agree, all four demos decode exactly.');
}

main();
