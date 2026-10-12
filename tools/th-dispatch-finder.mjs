#!/usr/bin/env node
// Locate the two-level ECL opcode dispatch in a Touhou executable, and check the known titles.
//
// Every title dispatches its enemy scripts the same way, with a guard on the opcode followed by a byte table and
// a jump table:
//
//     th12   0x415533  cmp   ecx, 0x163          first opcode 0x100, 356 permitted
//            0x41553f  movzx ecx, byte [ecx+0x419890]
//            0x415546  jmp   dword [ecx*4+0x419654]
//
//     th13   0x41b2b5 add   edx, -0x12c         first opcode 0x12c, 704 permitted
//            0x41b2c3 cmp   edx, 0x2bf
//            0x41b2cf movzx edx, byte [edx+0x41f9d8]
//            0x41b2d6 jmp   dword [edx*4+0x41f760]
// The former TH13 example at 0x463607 was ANM, not ECL. The opcode load's field
// offset and connection to this switch are now checked, not inferred from table size.
//
// so handler(op) = u32[jumpTable + byte[groupTable + (op - first)] * 4], and only `permitted` opcodes reach it.
// The finder does not assume any address: it searches the code section for the `jmp dword [reg*4 + disp32]` that
// is immediately preceded by a one-byte table load, then scores each candidate by how many targets are code and
// how many opcodes the byte table can actually reach.
//
//   node tools/th-dispatch-finder.mjs H:/Games/th/13/th13.exe           survey a title
//   node tools/th-dispatch-finder.mjs --check                            verify the recorded titles
//
// Usage: --check exits 1 if a recorded title's shape no longer matches what the executable says.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// What each title was measured to be. Adding a row is how a newly surveyed title becomes checked. first/last
// come from the guard instruction itself, which is the authority: the byte table can appear to reach further
// than the guard allows, and counting its reach over-reports (th14 measured 720 that way against a real 704).
const RECORDED = JSON.parse(fs.readFileSync(path.join(ROOT,'tools/ecl-dispatches.json'),'utf8'));
for (const row of Object.values(RECORDED)) {
  for (const key of ['jump','group','opcodeLoad']) row[key]=Number(row[key]);
  row.last=row.bound;
}

// The guard is two instructions: one that normalises the opcode to zero (`add reg, -first` or `sub reg, first`)
// and one that bounds it (`cmp reg, last`), followed by a conditional jump past the dispatch. They are not always
// adjacent and the bound uses a different opcode form (`cmp eax, imm32` is 3d, not 81 /7).
//
// Scanning the window byte by byte is unavoidable but it produces misaligned matches - th13 has 2d at both
// 0x4635ec and 0x4635ed, and the unaligned one sits closer to the table load. Choosing by proximity therefore
// picked garbage. Instead every plausible pair is tried and the pair is accepted only if the range it describes
// reaches a code handler for every one of its opcodes, which a misaligned pair cannot do.
function readGuard(img, loadAt, jump, group) {
  const firsts = [], lasts = [];
  for (let p = loadAt - 26; p <= loadAt - 5; p++) {
    if (p < 0) continue;
    const op0 = img.u8(p), op1 = img.u8(p + 1);
    // The short forms take eax and carry no ModRM byte, so their immediate starts one byte after the opcode.
    // The 81 /x forms do have a ModRM, so theirs starts two bytes after. Using one offset for both read the wrong
    // number for every title that uses the short form; th12 hid it by using 81 /7 for its bound.
    if (op0 === 0x05 || op0 === 0x2d || op0 === 0x3d) {
      const imm = img.u32(p + 1);
      if (op0 === 0x05) firsts.push({ at: p, value: (0 - imm) >>> 0 });
      else if (op0 === 0x2d) firsts.push({ at: p, value: imm >>> 0 });
      else lasts.push({ at: p, value: imm >>> 0 });
      continue;
    }
    if (op0 !== 0x81) continue;
    const imm = img.u32(p + 2);
    if ((op1 & 0xf8) === 0xc0) firsts.push({ at: p, value: (0 - imm) >>> 0 });
    else if ((op1 & 0xf8) === 0xe8) firsts.push({ at: p, value: imm >>> 0 });
    else if ((op1 & 0xf8) === 0xf8) lasts.push({ at: p, value: imm >>> 0 });
  }
  let best = null;
  for (const f of firsts) {
    if (f.value > 0x800) continue;                       // a real opcode base is small; garbage will not be
    for (const l of lasts) {
      if (l.value > 0x800 || l.at < f.at) continue;       // the bound follows the normalisation
      let ok = true;
      for (let i = 0; i <= l.value && ok; i++)
        ok = img.isCode(img.u32(jump + img.u8(group + i) * 4));
      if (!ok) continue;
      if (!best || f.at > best.normAt) best = { first: f.value, last: l.value, normAt: f.at, boundAt: l.at };
    }
  }
  return best;
}


function sections(buf) {
  const pe = buf.readUInt32LE(0x3c);
  const count = buf.readUInt16LE(pe + 6);
  const optSize = buf.readUInt16LE(pe + 20);
  const base = pe + 24 + optSize;
  const out = [];
  for (let i = 0; i < count; i++) {
    const s = base + i * 40;
    out.push({
      name: buf.toString('ascii', s, s + 8).replace(/\0.*$/, ''),
      va: buf.readUInt32LE(s + 12), vsize: buf.readUInt32LE(s + 8),
      raw: buf.readUInt32LE(s + 20), rawSize: buf.readUInt32LE(s + 16),
    });
  }
  return out;
}

// The image is not a flat VA slice - a VA in .rdata is not at its own file offset - so every read goes through
// the section table. A VA outside every mapped section reads as zero, which is what stops the length discovery.
function loader(exe) {
  const bytes = fs.readFileSync(exe);
  const pe = bytes.readUInt32LE(0x3c);
  const imageBase = bytes.readUInt32LE(pe + 24 + 28);
  const secs = sections(bytes);
  const secFor = (va) => secs.find((s) => va >= s.va + imageBase && va < s.va + imageBase + Math.max(s.vsize, s.rawSize));
  const at = (va) => { const s = secFor(va); return s ? s.raw + (va - imageBase - s.va) : -1; };
  return {
    bytes, imageBase, secs, secFor,
    u8: (va) => { const o = at(va); return o >= 0 && o < bytes.length ? bytes[o] : 0; },
    u32: (va) => { const o = at(va); return o >= 0 && o + 4 <= bytes.length ? bytes.readUInt32LE(o) : 0; },
    isCode: (va) => secFor(va)?.name === '.text',
  };
}

function findCandidates(img) {
  const text = img.secs.find((s) => s.name === '.text');
  const start = text.raw, end = text.raw + text.rawSize;
  const vaOf = (offset) => offset - text.raw + text.va + img.imageBase;
  const hits = [];
  for (let i = start; i + 12 <= end; i++) {
    // `jmp dword [reg*4 + disp32]` is FF /4 with a SIB byte whose scale is 4 and whose base is none, so the
    // ModRM is mod=00, reg=100 and the SIB has index=<reg>, base=101. Checking only the ecx form (`ff 24 8d`)
    // found nothing in titles from th14 on, which dispatch through a different register.
    if (img.bytes[i] !== 0xff || (img.bytes[i + 1] & 0xf8) !== 0x20) continue;
    const sib = img.bytes[i + 2];
    if ((sib & 0xc0) !== 0x80 || (sib & 0x07) !== 0x05) continue;
    // Newer compilers insert register/stack moves between the table load and jump.
    for (let back = 7; back <= 32; back++) {
      const p = i - back;
      if (p < start || img.bytes[p] !== 0x0f || img.bytes[p + 1] !== 0xb6) continue;
      // Any base register with disp32, not only eax/ecx. TH13 ECL uses edx.
      if ((img.bytes[p + 2] & 0xc0) !== 0x80 || (img.bytes[p + 2] & 7) === 4) continue;
      hits.push({ at: vaOf(i), jump: img.bytes.readUInt32LE(i + 3), group: img.bytes.readUInt32LE(p + 3), loadAt: vaOf(p) });
      break;
    }
  }
  return hits;
}

// A candidate is scored by what its tables actually contain: how many consecutive targets are code, and how many
// opcodes the byte table can reach without indexing past the end of that target table.
function score(img, jump, group) {
  const targets = [];
  for (let i = 0; i < 0x400; i++) { const t = img.u32(jump + i * 4); if (!img.isCode(t)) break; targets.push(t); }
  let permitted = 0;
  if (targets.length) for (let i = 0; i < 0x400; i++) { if (img.u8(group + i) >= targets.length) break; permitted++; }
  return { targets, permitted, distinct: new Set(targets).size };
}

function survey(exe) {
  const img = loader(exe);
  return findCandidates(img)
    .map((h) => ({ ...h, ...score(img, h.jump, h.group) }))
    .sort((a, b) => b.permitted * b.targets.length - a.permitted * a.targets.length);
}

// The opcode -> handler map for one title, read through the guard and the two tables. Every entry is a measured
// address: nothing here is inferred from the decompiled C, which has fewer case labels than there are handlers.
function opcodeMap(want) {
  const img = loader(want.exe);
  const targets = [];
  for (let i = 0; i < 0x400; i++) { const t = img.u32(want.jump + i * 4); if (!img.isCode(t)) break; targets.push(t); }
  const opcodes = {};
  const span = want.last + 1;
  for (let i = 0; i < span; i++) opcodes['0x' + (want.first + i).toString(16)] = '0x' + targets[img.u8(want.group + i)].toString(16);
  return {
    title: want.game ?? null, domain: want.domain, first: '0x' + want.first.toString(16), permitted: span,
    lastOpcode: '0x' + (want.first + span - 1).toString(16),
    jumpTable: '0x' + want.jump.toString(16), groupTable: '0x' + want.group.toString(16),
    targets: targets.length, distinct: new Set(targets).size, opcodes,
  };
}

function main() {
  const check = process.argv.includes('--check');
  const emitAt = process.argv.indexOf('--emit') >= 0 ? process.argv[process.argv.indexOf('--emit') + 1] : null;
  const exe = process.argv[2];

  if (emitAt) {
    const out = {};
    for (const [name, want] of Object.entries(RECORDED)) out[name] = opcodeMap({ ...want, game: name });
    fs.writeFileSync(emitAt, JSON.stringify(out, null, 2) + '\n');
    const lines = Object.entries(out).map(([n, m]) => `  ${n}: ${m.permitted} opcodes, ${m.distinct} distinct handlers, ${m.first}..${m.lastOpcode}`);
    console.log(`wrote ${emitAt}\n` + lines.join('\n'));
    return;
  }

  if (check || !exe) {
    let bad = 0;
    for (const [name, want] of Object.entries(RECORDED)) {
      if (!fs.existsSync(want.exe)) { console.log(`  ${name}: SKIP (no executable at ${want.exe})`); continue; }
      const img = loader(want.exe);
      const problems = [];
      const loadBytes=Array.from({length:4},(_,i)=>img.u8(want.opcodeLoad+i).toString(16).padStart(2,'0')).join('');
      if(want.domain!=='ECL'||loadBytes!==want.opcodeBytes)problems.push('ECL opcode load (+4) does not match its verified instruction');
      // The candidate must be found by the search, not just assumed at its recorded address: a record that no
      // longer matches any real dispatch instruction is exactly what this gate is for.
      const candidate = findCandidates(img).find((c) => c.jump === want.jump && c.group === want.group);
      if (!candidate) problems.push(`no dispatch instruction found using jump=0x${want.jump.toString(16)} group=0x${want.group.toString(16)}`);
      if(candidate&&(candidate.loadAt<=want.opcodeLoad||candidate.loadAt-want.opcodeLoad>0x50))problems.push('opcode load is not in this dispatch block');
      const guard = candidate ? readGuard(img, candidate.loadAt, candidate.jump, candidate.group) : null;
      if (candidate && !guard) problems.push('could not read the guard instruction');
      if (guard && guard.first !== want.first)
        problems.push(`guard normalises to first opcode 0x${guard.first.toString(16)}, recorded 0x${want.first.toString(16)}`);
      if (guard && guard.last !== want.last) problems.push(`guard bound ${guard.last} differs from ${want.last}`);
      const targets = [];
      for (let i = 0; i < 0x400; i++) { const t = img.u32(want.jump + i * 4); if (!img.isCode(t)) break; targets.push(t); }
      if (targets.length !== want.targets) problems.push(`target table has ${targets.length} entries, recorded ${want.targets}`);
      const span = want.last + 1;
      for (let i = 0; i < span; i++) {
        const t = img.u32(want.jump + img.u8(want.group + i) * 4);
        if (!img.isCode(t)) { problems.push(`opcode 0x${(want.first + i).toString(16)} indexes a target that is not code`); break; }
      }
      if (problems.length) { bad++; console.log(`  ${name}: FAIL - ${problems.join('; ')}`); }
      else console.log(`  ${name}: ok  first=0x${want.first.toString(16)} permitted=${span} jump=0x${want.jump.toString(16)}` +
        ` group=0x${want.group.toString(16)} targets=${targets.length} distinct=${new Set(targets).size}`);
    }
    process.exit(bad ? 1 : 0);
  }

  const img = loader(exe);
  console.log(`  ${exe}`);
  for (const c of survey(exe).slice(0, 6)) {
    const guard = readGuard(img, c.loadAt, c.jump, c.group);
    console.log(`    jmp @0x${c.at.toString(16)} jump=0x${c.jump.toString(16)} group=0x${c.group.toString(16)}` +
      ` codeTargets=${c.targets.length} distinct=${c.distinct} reach=${c.permitted}` +
      (guard ? `  guard: first=0x${guard.first.toString(16)}` : '  guard: unread'));
  }
}

main();
