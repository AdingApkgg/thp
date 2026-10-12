// Builds the TH12 extended-opcode work map.
//
// TH12's ECL interpreter is `FUN_004154d0` (th12-decomp). It dispatches on the
// instruction's `id` field over 0x100..0x263 and calls one shared body per
// `switchD_*` label. The portable engine currently routes the same numbers with
// TH11's table (EnemyScript.cpp), so a TH12 opcode can land in a TH11 handler
// that means something else entirely. That is silent, not loud: it was the cause
// of the divide-by-zero trap found while booting stage 1.
//
// This tool joins four sources so the remaining work is enumerated rather than
// discovered by crashing:
//   1. FUN_004154d0's case bodies          -> which TH12 opcodes exist and what
//                                             shape each body has
//   2. docs/th12/ecl-opcodes.json          -> TH12 signatures and TH11 deltas
//   3. the engine's handler sources        -> which numbers the engine handles
//   4. the verification artifact           -> which opcodes th12.dat really uses
//
// Usage: node tools/th12-opcode-map.mjs [--check]
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..');
const DECOMP = resolve(repo, 'reference/th12-decomp/decomp_out/FUN_004154d0_004154d0.c');
const OUT = resolve(repo, 'docs/th12/ecl-extended-opcodes.json');
const OPCODES = resolve(repo, 'docs/th12/ecl-opcodes.json');
const GAME = resolve(repo, 'runtimes/th12/th12_web/cpp/game');
const USAGE = resolve(repo, 'runtimes/th12/th12_web/artifacts/cpp/verification/th12-ecl-opcodes.json');

if (!existsSync(DECOMP)) {
  console.error(`missing ${DECOMP} - the map is built from the th12 Ghidra corpus under reference/`);
  process.exit(2);
}

const opcodeTable = JSON.parse(readFileSync(OPCODES, 'utf8'));
const signature = new Map(opcodeTable.entries.map(e => [e.id, e.signature]));
const provenance = new Map(opcodeTable.entries.map(e => [e.id, e.from]));
const th11 = new Map(opcodeTable.entries.map(e => [e.id, e.th11]));

// --- 1. case bodies -------------------------------------------------------
const lines = readFileSync(DECOMP, 'utf8').split('\n');
const nodes = [];
for (let i = 0; i < lines.length; i++) {
  const c = lines[i].match(/^\s*case (0x[0-9a-fA-F]+):\s*$/);
  const l = lines[i].match(/^\s*(switchD_[0-9a-fA-F]+_caseD_[0-9a-fA-F]+):\s*$/);
  if (c) nodes.push({ line: i, kind: 'case', id: parseInt(c[1], 16), label: null });
  else if (l) nodes.push({ line: i, kind: 'label', id: null, label: l[1] });
}
const bodies = new Map(); // id -> shape
const labelBodies = new Map();
const caseOrder = [];
for (let i = 0; i < nodes.length; i++) {
  const from = nodes[i].line + 1;
  const to = i + 1 < nodes.length ? nodes[i + 1].line : lines.length;
  const body = lines.slice(from, to).map(s => s.trim()).filter(Boolean);
  if (nodes[i].kind === 'label') { labelBodies.set(nodes[i].label, body); continue; }
  const only = body.length === 1 ? body[0] : null;
  let shape;
  if (only === 'break;') shape = { kind: 'noop' };
  else if (only && /^goto (\w+);$/.test(only)) shape = { kind: 'shared', label: only.slice(5, -1), lines: labelBodies.get(only.slice(5, -1))?.length ?? null };
  // Ghidra prints grouped cases as consecutive `case X:` lines: every case but
  // the last has an empty body and falls through to the next one.
  else if (body.length === 0) shape = { kind: 'fallthrough', into: null };
  else shape = { kind: 'inline', lines: body.length };
  bodies.set(nodes[i].id, shape);
  caseOrder.push(nodes[i].id);
}
// Resolve fall-through chains (a grouped case inherits the next case's shape).
for (let i = 0; i < caseOrder.length; i++) {
  const shape = bodies.get(caseOrder[i]);
  if (shape.kind !== 'fallthrough') continue;
  const next = bodies.get(caseOrder[i + 1]);
  if (next) { shape.into = caseOrder[i + 1]; shape.resolvedTo = next.kind; }
}
// Resolve one level of sharing so a shared body's own shape is visible.
for (const [id, shape] of bodies) {
  if (shape.kind !== 'shared') continue;
  const body = labelBodies.get(shape.label);
  const only = body && body.length === 1 ? body[0] : null;
  shape.sharedBodyIsNoop = only === 'break;';
  shape.sharedBodyCalls = [...new Set((body ?? []).flatMap(l => [...l.matchAll(/FUN_[0-9a-f]{8}/g)].map(m => m[0])))].length;
}

// --- 2. routing + handlers in the engine ----------------------------------
function opcodesIn(file) {
  const text = readFileSync(resolve(GAME, file), 'utf8');
  const found = new Set();
  for (const m of text.matchAll(/case (0x[0-9a-fA-F]+)/g)) found.add(parseInt(m[1], 16));
  for (const m of text.matchAll(/\bop\s*==\s*(0x[0-9a-fA-F]+)/g)) found.add(parseInt(m[1], 16));
  return found;
}
const handlerFiles = readdirSync(GAME).filter(f => /^Enemy.*\.cpp$/.test(f)).sort();
const handled = new Map();
for (const f of handlerFiles) for (const id of opcodesIn(f)) {
  if (!handled.has(id)) handled.set(id, []);
  handled.get(id).push(f);
}

// `EnemyScript.cpp` chooses which handler family runs for a given opcode.
const routing = readFileSync(resolve(GAME, 'EnemyScript.cpp'), 'utf8');
// Opcodes the engine answers through a dispatch gate instead of a case label. Every entry names the
// file and the exact fragment that must be present; the loop below throws if the code stops matching,
// so this stays a verified claim and never becomes a hand-edited verdict.
const MANAGER_GATES = [
    { opcode: 257, file: 'EnemyManager.cpp', evidence: 'op!=0x101', why: 'the spawn gate; command() reads the name at instruction+20 and the arguments through the same bit-test-and-resolve helpers TH12 uses' },
];
for (const gate of MANAGER_GATES) {
    const source = readFileSync(resolve(resolve(repo, 'runtimes/th12/th12_web/cpp/game'), gate.file), 'utf8');
    if (!source.includes(gate.evidence)) throw new Error(`gate evidence missing for 0x${gate.opcode.toString(16)}: ${gate.file} / ${gate.evidence}`);
    if (!handled.has(gate.opcode)) handled.set(gate.opcode, []);
    if (!handled.get(gate.opcode).includes(gate.file)) handled.get(gate.opcode).push(gate.file);
}
const routedManagers = /op>=0x100&&op<=0x10f/.test(routing);

// The engine's refusal list is the other half of the contract. A collision the
// engine now transcribes on purpose must stop being classed as unhandled, or the
// coverage test cannot tell "still refused" from "silently running th11 code".
const refusedMatch = routing.match(/kTh12CollidingOpcodes\[\]\s*=\s*\{([^}]*)\}/);
if (!refusedMatch) throw Error('EnemyScript.cpp no longer declares kTh12CollidingOpcodes');
const refused = new Set((refusedMatch[1].match(/\d+/g) ?? []).map(Number));

// --- 3. real usage --------------------------------------------------------
const usage = existsSync(USAGE) ? JSON.parse(readFileSync(USAGE, 'utf8')) : null;
const count = new Map((usage?.usedOpcodes ?? []).map(e => [e.id, e.count]));

// --- 4. verdict -----------------------------------------------------------
const extended = [...signature.keys()].filter(id => id >= 256).sort((a, b) => a - b);
const entries = extended.map(id => {
  const delta = th11.get(id) ?? 'new';
  const used = count.get(id) ?? 0;
  const body = bodies.get(id) ?? null;
  // A TH12 opcode is only safely reusing a TH11 handler if the signature is
  // unchanged; anything else is a collision that currently runs the wrong code.
  const collision = used > 0 && delta !== 'new' && delta !== 'same';
  return {
    id,
    signature: signature.get(id),
    provenance: provenance.get(id),
    th11: delta,
    usedInTh12Dat: used,
    decompiled: body ? body.kind : 'absent',
    ...(body?.kind === 'fallthrough' ? { fallsThroughTo: body.into, resolvesAs: bodies.get(body.into)?.kind } : {}),
    ...(body?.kind === 'shared' ? { sharedLabel: body.label, sharedBodyIsNoop: body.sharedBodyIsNoop, sharedBodyCalls: body.sharedBodyCalls } : {}),
    engineHandles: handled.has(id) ? handled.get(id) : [],
    verdict: (body?.kind === 'noop' || (body?.kind === 'fallthrough' && bodies.get(body.into)?.kind === 'noop')) ? 'noop-in-original'
      : collision ? (refused.has(id) ? 'collision' : 'implemented-collision')
      : handled.has(id) ? 'implemented'
      : used > 0 ? 'todo'
      : 'unused',
    ...(collision && !refused.has(id) ? { implementedNotRefused: true } : {}),
  };
});

const byVerdict = {};
for (const e of entries) byVerdict[e.verdict] = (byVerdict[e.verdict] ?? 0) + 1;
const collisions = entries.filter(e => e.verdict === 'collision');
const usedTodo = entries.filter(e => e.usedInTh12Dat > 0 && e.verdict === 'todo');
const noops = entries.filter(e => e.verdict === 'noop-in-original');

const artifact = {
  game: 'th12',
  source: {
    interpreter: 'th12-decomp FUN_004154d0 @ 0x4154d0 (173 cases, switch range 0x100..0x263)',
    routing: 'runtimes/th12/th12_web/cpp/game/EnemyScript.cpp (TH11 numbers, needs re-derivation)',
    signatures: 'docs/th12/ecl-opcodes.json',
  },
  counts: {
    extendedIds: extended.length,
    casesInOriginal: bodies.size,
    usedExtendedInTh12Dat: entries.filter(e => e.usedInTh12Dat > 0).length,
    byVerdict,
  },
  routedByTh11Table: routedManagers,
  refusedByEngine: [...refused].sort((a, b) => a - b),
  entries,
};

const text = JSON.stringify(artifact, null, 2) + '\n';
if (process.argv.includes('--check')) {
  if (!existsSync(OUT)) { console.error(`${OUT} missing - run without --check`); process.exit(1); }
  if (readFileSync(OUT, 'utf8') !== text) { console.error(`${OUT} is stale - rerun the generator`); process.exit(1); }
  console.log(`th12 extended opcode map: ${extended.length} ids, up to date`);
} else {
  writeFileSync(OUT, text);
  console.log(`wrote ${OUT}`);
  console.log(`  extended ids: ${extended.length}, decompiled cases: ${bodies.size}`);
  console.log(`  verdicts: ${JSON.stringify(byVerdict)}`);
  console.log(`  used by th12.dat and still todo: ${usedTodo.length}`);
  console.log(`  collisions (TH12 signature differs from the TH11 handler it reaches): ${collisions.length}`);
  console.log(`  no-ops in the original: ${noops.map(e => e.id).join(', ') || '(none)'}`);
}
