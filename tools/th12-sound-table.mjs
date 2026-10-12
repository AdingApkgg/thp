// Recover TH12's sound-effect sample table from th12.exe and check the engine's
// copy against it.
//
// th12.exe keeps the table at .data 0x4aea50: 49 consecutive pointers into
// .rdata, each naming a "se_*.wav" entry. That order matches th12.dat's archive
// order one for one, which is what makes it trustworthy as the sample list.
//
//   node tools/th12-sound-table.mjs            # print the recovered table
//   node tools/th12-sound-table.mjs --check    # verify SoundEffects.cpp agrees
//
// --check is the gate: it fails if the hardcoded array drifts from the original
// binary's table, or if any listed sample is absent from th12.dat.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const EXE = 'H:/Games/th/12/th12.exe';
const DAT = 'H:/Games/th/12/th12.dat';
const THDAT = resolve(root, 'tools/thtk/extracted/thtk-bin-12/thdat.exe');
const SOURCE = resolve(root, 'runtimes/th12/th12_web/cpp/game/SoundEffects.cpp');
const TABLE_VA = 0x4aea50;
const COUNT = 49;

function recover() {
  const b = readFileSync(EXE);
  const lfanew = b.readUInt32LE(0x3c);
  const sections = [];
  const table = lfanew + 0x18 + b.readUInt16LE(lfanew + 0x14);
  for (let i = 0; i < b.readUInt16LE(lfanew + 6); i++) {
    const o = table + i * 40;
    sections.push({
      name: b.toString('ascii', o, o + 8).replace(/\0/g, ''),
      vsize: b.readUInt32LE(o + 8), rva: b.readUInt32LE(o + 12),
      rawSize: b.readUInt32LE(o + 16), raw: b.readUInt32LE(o + 20),
    });
  }
  const va2off = va => {
    for (const s of sections) {
      if (va >= 0x400000 + s.rva && va < 0x400000 + s.rva + Math.min(s.vsize, s.rawSize))
        return s.raw + (va - 0x400000 - s.rva);
    }
    throw Error(`address 0x${va.toString(16)} is in no section`);
  };
  const cstr = off => { let end = off; while (b[end] !== 0) end++; return b.toString('latin1', off, end); };
  const base = va2off(TABLE_VA);
  const names = [];
  for (let i = 0; i < COUNT; i++) {
    const name = cstr(va2off(b.readUInt32LE(base + i * 4)));
    if (!/^se_[a-z0-9_]+\.wav$/.test(name)) throw Error(`entry ${i} is not a se_ name: ${name}`);
    names.push(name);
  }
  return names;
}

const recovered = recover();

if (!process.argv.includes('--check')) {
  console.log(`TH12 SE sample table, recovered from th12.exe .data 0x${TABLE_VA.toString(16)} (${recovered.length} entries):`);
  recovered.forEach((n, i) => console.log(`  ${String(i).padStart(2)} ${n}`));
  process.exit(0);
}

const problems = [];

// 1. the engine's array must equal the original's, in order
const source = readFileSync(SOURCE, 'utf8');
const block = /const char\* const sound_samples\[(\d+)\]\s*=\s*\{([^}]*)\}/.exec(source);
if (!block) problems.push('SoundEffects.cpp: could not find the sound_samples array');
else {
  const declared = Number(block[1]);
  const listed = [...block[2].matchAll(/"([^"]+)"/g)].map(m => m[1]);
  if (declared !== recovered.length) problems.push(`declared size ${declared} != recovered ${recovered.length}`);
  if (listed.length !== recovered.length) problems.push(`array has ${listed.length} names, recovered ${recovered.length}`);
  for (let i = 0; i < Math.min(listed.length, recovered.length); i++) {
    if (listed[i] !== recovered[i]) problems.push(`entry ${i}: engine has ${listed[i]}, original has ${recovered[i]}`);
  }
  if (new Set(listed).size !== new Set(recovered).size) problems.push('engine list is missing or duplicating names');

  // 2. every sample the engine will load must actually ship in th12.dat
  const archive = execFileSync(THDAT, ['-l', 'd', DAT], { encoding: 'utf8' });
  const shipped = new Set(archive.split('\n').map(l => l.split(/\s+/)[0]).filter(n => /^se_.*\.wav$/.test(n)));
  for (const name of new Set(listed)) if (!shipped.has(name)) problems.push(`th12.dat does not ship ${name}`);
}

if (problems.length) {
  console.error(`th12 sound table: ${problems.length} problem(s)`);
  for (const p of problems) console.error('  - ' + p);
  process.exit(1);
}
console.log(`th12 sound table: OK — ${recovered.length} samples match th12.exe .data 0x${TABLE_VA.toString(16)} and all ship in th12.dat`);
