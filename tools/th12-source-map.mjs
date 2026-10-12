// Build a th12.exe "function -> original source file" map.
//
// th12.exe (MSVC 2008, no PDB) embeds ZUN's assert/`__FILE__` literals such as
// `.\src\game\effect.cpp:391`. Each literal lives in .rdata and is pushed as an
// immediate by the function that asserts. Matching those pushes against the
// Ghidra delink corpus in `reference/th12-decomp/decomp_out` (one file per
// function, named `<symbol>_<address>.c`) recovers which original translation
// unit every function came from.
//
// Usage: node tools/th12-source-map.mjs [exePath] [outJson]
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

const ws = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const exe = process.argv[2] ?? 'H:/Games/th/12/th12.exe';
const outJson = process.argv[3] ?? resolve(ws, 'docs/th12/th12-function-map.json');
const decomp = resolve(ws, 'reference/th12-decomp/decomp_out');

// ---------------------------------------------------------------- PE sections
const buf = readFileSync(exe);
const pe = buf.readUInt32LE(0x3c);
const imageBase = buf.readUInt32LE(pe + 0x34);
const nSections = buf.readUInt16LE(pe + 0x6);
const optSize = buf.readUInt16LE(pe + 0x14);
const sections = [];
for (let i = 0; i < nSections; i++) {
  const s = pe + 24 + optSize + i * 40;
  sections.push({
    name: buf.toString('latin1', s, s + 8).replace(/\0.*$/, ''),
    virtualSize: buf.readUInt32LE(s + 8),
    rva: buf.readUInt32LE(s + 12),
    rawSize: buf.readUInt32LE(s + 16),
    raw: buf.readUInt32LE(s + 20),
    flags: buf.readUInt32LE(s + 36),
  });
}
const rvaToOffset = rva => {
  for (const s of sections) if (rva >= s.rva && rva < s.rva + Math.max(s.rawSize, s.virtualSize)) return s.raw + (rva - s.rva);
  return null;
};
const offsetToVa = off => {
  for (const s of sections) if (off >= s.raw && off < s.raw + s.rawSize) return imageBase + s.rva + (off - s.raw);
  return null;
};
const text = sections.find(s => s.name === '.text');
const textStart = text.raw, textEnd = text.raw + text.rawSize;

// ------------------------------------------------- path literals in .rdata/.data
const pathRe = /[\x20-\x7e]{6,}/g;
const latin = buf.toString('latin1');
const literals = [];
let m;
while ((m = pathRe.exec(latin))) {
  const s = m[0];
  if (!/\.(cpp|h|inc|c)\b/.test(s)) continue;
  if (!/src[\\/]/.test(s)) continue;
  const va = offsetToVa(m.index);
  if (va === null) continue;
  const file = (s.match(/([^\\/]+\.(?:cpp|h|inc|c))\b/) || [])[1];
  if (file) literals.push({ va, s, file });
}
const byVa = new Map(literals.map(l => [l.va, l]));

// --------------------------------------------------------- pushes referencing them
// A literal is not always referenced at its first byte: the original assert
// helper takes the file name and then the message, and MSVC folds the whole
// `"\\src\\game\\x.cpp:LINE message"` text into one blob, so the code may push
// `literal + k`. Match every immediate that lands anywhere inside a literal.
const immediates = new Map(); // value -> [ .text file offsets ]
for (let p = textStart; p + 4 <= textEnd; p++) {
  const v = buf.readUInt32LE(p);
  if (v < 0x498000 || v >= 0x4ae000) continue;
  if (!immediates.has(v)) immediates.set(v, []);
  immediates.get(v).push(p);
}
const refs = [];
for (const l of literals) {
  for (let k = 0; k <= l.s.length; k++) {
    const sites = immediates.get(l.va + k);
    if (!sites) continue;
    for (const site of sites) refs.push({ site: offsetToVa(site), stringVa: l.va, offset: k, file: l.file });
  }
}

// ------------------------------------------------------------ function directory
const functions = [];
for (const f of readdirSync(decomp)) {
  const mm = /_([0-9a-fA-F]{8})\.c$/.exec(f);
  if (mm) functions.push(parseInt(mm[1], 16) + imageBase);
}
functions.sort((a, b) => a - b);
const ownerOf = va => {
  let lo = 0, hi = functions.length - 1, best = null;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (functions[mid] <= va) { best = functions[mid]; lo = mid + 1; } else hi = mid - 1; }
  return best;
};

const map = new Map();
for (const r of refs) {
  const owner = ownerOf(r.site);
  if (owner === null) continue;
  const key = owner;
  if (!map.has(key)) map.set(key, { function: '0x' + owner.toString(16).padStart(8, '0'), files: {}, sites: [] });
  const e = map.get(key);
  e.files[r.file] = (e.files[r.file] ?? 0) + 1;
  e.sites.push({ at: '0x' + r.site.toString(16).padStart(8, '0'), file: r.file, literal: byVa.get(r.stringVa).s });
}

const entries = [...map.values()].sort((a, b) => Number(a.function) - Number(b.function));
const fileTally = {};
for (const e of entries) for (const [f, n] of Object.entries(e.files)) fileTally[f] = (fileTally[f] ?? 0) + n;

mkdirSync(dirname(outJson), { recursive: true });
writeFileSync(outJson, JSON.stringify({
  source: { exe, imageBase: '0x' + imageBase.toString(16), text: { rva: text.rva, rawSize: text.rawSize } },
  counts: { pathLiterals: literals.length, distinctFiles: new Set(literals.map(l => l.file)).size, pushReferences: refs.length, functionsWithFile: entries.length, knownFunctions: functions.length },
  fileTally,
  literals: literals.map(l => ({ va: '0x' + l.va.toString(16), file: l.file, literal: l.s })),
  functions: entries,
}, null, 2) + '\n');

console.log(JSON.stringify({
  pathLiterals: literals.length,
  distinctFiles: new Set(literals.map(l => l.file)).size,
  pushReferences: refs.length,
  functionsWithFile: entries.length,
  knownFunctions: functions.length,
  out: outJson,
}, null, 2));
