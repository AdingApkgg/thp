// Extracts the TH12 ECL opcode signature table from thtk's thecl10.c.
//
// thtk knows which opcode ids exist in TH12 and how many arguments each one
// takes, but not their names - it prints `ins_N` without a community eclmap.
// The id list plus argument grammar is still exactly what a portable engine
// needs to stop misdecoding the bytecode, so it is captured here as a reviewed
// artifact rather than transcribed by hand.
//
// Usage: node tools/th12-ecl-opcodes.mjs [--check]
//   writes  docs/th12/ecl-opcodes.json
//   --check fails if the checked-in file does not match a fresh extraction.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');
const SOURCE = resolve(repo, 'reference/thtk/thecl/thecl10.c');
const OUT = resolve(repo, 'docs/th12/ecl-opcodes.json');

if (!existsSync(SOURCE)) {
  console.error(`missing ${SOURCE} - the table is generated from the thtk checkout under reference/`);
  process.exit(2);
}

const lines = readFileSync(SOURCE, 'utf8').split('\n');

function table(name) {
  const start = lines.findIndex(l => l.includes(`id_format_pair_t ${name}[]`));
  if (start < 0) throw new Error(`table ${name} not found`);
  const out = [];
  for (let i = start + 1; i < lines.length; i++) {
    if (/^\s*\};/.test(lines[i])) break;
    const m = lines[i].match(/\{\s*(-?\d+)\s*,\s*"([^"]*)"\s*\}/);
    if (m) out.push({ id: Number(m[1]), signature: m[2] });
  }
  return out;
}

const th12 = table('th12_fmts');
const th11 = table('th11_fmts');
const alcostg = table('alcostg_fmts');
const th10 = table('th10_fmts');

// thtk resolves a signature by walking a fall-through chain and taking the
// first hit, so the effective table for a version is a priority merge, not a
// single array. TH12 is `th12 -> th11 -> alcostg -> th10`; TH11 skips the
// first step. Reproduce that here or the diff is meaningless.
function effective(chain) {
  const map = new Map();
  for (const [label, tbl] of chain) {
    for (const e of tbl) if (!map.has(e.id)) map.set(e.id, { id: e.id, signature: e.signature, from: label });
  }
  return [...map.values()].sort((a, b) => a.id - b.id);
}
const eff12 = effective([['th12_fmts', th12], ['th11_fmts', th11], ['alcostg_fmts', alcostg], ['th10_fmts', th10]]);
const eff11 = effective([['th11_fmts', th11], ['alcostg_fmts', alcostg], ['th10_fmts', th10]]);

const prev = Object.fromEntries(eff11.map(e => [e.id, e.signature]));
const entries = eff12.map(e => ({
  id: e.id,
  signature: e.signature,
  parameters: e.signature.length,
  from: e.from,
  // What TH11 resolved this id to. `new` means TH11 had no such opcode at all,
  // so the instruction cannot appear in a TH11 script.
  th11: e.id in prev ? (prev[e.id] === e.signature ? 'same' : `was "${prev[e.id]}"`) : 'new',
}));

const added = entries.filter(e => e.th11 === 'new');
const coreAdded = added.filter(e => e.id < 256);
const coreChanged = entries.filter(e => e.id < 256 && e.th11 !== 'same' && e.th11 !== 'new');
const droppedById = Object.keys(prev).map(Number).filter(id => !entries.some(e => e.id === id)).sort((a, b) => a - b);

// Document the argument grammar so the artifact is readable on its own.
// Taken from the `case` labels of thtk's argument printer (thecl10.c).
const GRAMMAR = {
  S: 'signed integer',
  f: 'float',
  o: 'byte offset relative to this instruction',
  t: 'time value (float)',
  m: 'name/string reference',
  D: 'thread descriptor',
  '*': 'repeat marker: preceding argument is a count',
  d: 'signed integer (short form)',
  F: 'float (short form)',
  M: 'name reference (short form)',
};
// Only keep grammar entries that actually occur in the table.
const usedChars = [...new Set(eff12.flatMap(e => [...e.signature]))].sort();
const grammar = Object.fromEntries(usedChars.map(c => [c, GRAMMAR[c] ?? 'unknown']));

const artifact = {
  game: 'th12',
  source: 'thtk thecl10.c th12_fmts[]',
  sourceUrl: 'https://github.com/thpatch/thtk',
  note: 'Opcode ids and argument grammars; argument names/semantics require the original binary.',
  flagCharCount: usedChars.length,
  grammar,
  count: entries.length,
  th11Comparison: {
    resolvedByIdForTh12Only: added.length,
    coreIdsAddedBelow256: coreAdded.map(e => e.id),
    coreIdsChangedBelow256: coreChanged.map(e => ({ id: e.id, th12: e.signature, th11: e.th11 })),
    idsTh11HadThatTh12DoesNot: droppedById,
  },
  idBlocks: (() => {
    const blocks = [];
    let run = null;
    for (const e of entries) {
      if (run && e.id === run.end + 1) run.end = e.id;
      else { run = { start: e.id, end: e.id }; blocks.push(run); }
    }
    return blocks.map(b => (b.start === b.end ? `${b.start}` : `${b.start}-${b.end}`));
  })(),
  entries,
};

const text = JSON.stringify(artifact, null, 2) + '\n';
if (process.argv.includes('--check')) {
  if (!existsSync(OUT)) { console.error(`${OUT} missing - run without --check`); process.exit(1); }
  if (readFileSync(OUT, 'utf8') !== text) { console.error(`${OUT} is stale - rerun the generator`); process.exit(1); }
  console.log(`th12 ecl opcode table: ${entries.length} entries, up to date`);
} else {
  writeFileSync(OUT, text);
  console.log(`wrote ${OUT}`);
  console.log(`  ${entries.length} opcodes, blocks: ${artifact.idBlocks.join(', ')}`);
  console.log(`  grammar chars: ${usedChars.join(' ')}`);
}
