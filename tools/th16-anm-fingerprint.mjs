// Identify each native context offset with the port offset that behaves like it, by what changes.
//
// The checker derives its mapping by whole-sequence value equality over 4684 cases, and value equality
// is a hard test across a rebuilt structure: only quantities whose values coincide verbatim - constants
// and a few counters - can pass it, which is why five of ninety slots were identified. This runs the
// same corpus with the pre-state the oracle now records and compares what each offset does across all of
// them: for every native offset, the bit vector "did this word change in this case", and for every
// port offset, the same bit vector measured through the fixture's own reset/step phases. A port body is
// not needed for this: what is compared is the shape of the change, whatever produced it.
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const rt = resolve(root, 'runtimes/th12/th12_web');
const out = resolve(root, 'artifacts/th16/fingerprint');
const doc = resolve(root, 'docs/porting');
const clang = resolve(root, 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const sources = ['AnmInterpreter', 'AnmVm', 'AnmGeometry', 'Interpolation', 'AnmResource']
    .map(s => `cpp/game/${s}.cpp`);
const fixture = 'tests/cpp/th16-anm-fixture.cpp';
mkdirSync(out, {recursive: true});

const report = JSON.parse(readFileSync(resolve(root, 'artifacts/th16/anm-native-all.json'), 'utf8'));
const cases = report.cases.filter(c => !c.fault);
// The report's measured.snapshot field reads 0x1792 while every case carries 3584 hex characters, so
// the length the comparison can trust is the cases' own snapshot; the field is noted, not used.
const snapshot = cases[0].before.length / 2;
if (cases.some(c2 => c2.before.length / 2 !== snapshot))
    throw new Error('the corpus snapshots differ in length');
if (!cases.length || !cases[0].before) throw new Error('the corpus carries no before state');
console.log(`corpus: ${report.cases.length} cases, ${cases.length} without fault, snapshot 0x${snapshot.toString(16)}`
    + ` (the report's measured.snapshot field says ${report.measured.snapshot})`);

// --- the native side: for each offset, the bit vector of "changed in this case"
const nativeWords = cases.map(row => [Buffer.from(row.before, 'hex'), Buffer.from(row.context, 'hex')]);
const changedCount = o => nativeWords.reduce((n, [b, a]) => n + (b.readUInt32LE(o) === a.readUInt32LE(o) ? 0 : 1), 0);
const varyingNative = [];
for (let o = 0; o + 4 <= snapshot; o += 4) {
    const bits = Uint8Array.from(nativeWords,
        ([b, a]) => (b.readUInt32LE(o) === a.readUInt32LE(o) ? 0 : 1));
    const n = bits.reduce((x, y) => x + y, 0);
    if (n > 0 && n < cases.length) varyingNative.push({offset: o, bits, changed: n});
}
console.log(`native offsets that change in some cases and not in others: ${varyingNative.length}`
    + ` (0x18 ${changedCount(0x18)}, 0x28 ${changedCount(0x28)}, 0x544 ${changedCount(0x544)})`);

// --- the port side, through the fixture's own two phases
const wasm = resolve(out, 'fingerprint.wasm');
execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
    '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--export-memory', '-DPORT_TITLE=16',
    ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
    {cwd: rt, stdio: 'pipe', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync(wasm), {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const words = (c.size() >>> 0) >> 2;
const portBits = [];
for (let w = 0; w < words; w++) portBits.push(new Uint8Array(cases.length));
for (const [i, row] of cases.entries()) {
    c.reset(row.value | 0, row.variant);
    const pre = new Uint32Array(words);
    for (let w = 0; w < words; w++) pre[w] = c.slot(w * 4) >>> 0;
    // The fixture's macro names the export after its argument, so the execution phase is `step`.
    c.step(row.op, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
    for (let w = 0; w < words; w++)
        portBits[w][i] = pre[w] === (c.slot(w * 4) >>> 0) ? 0 : 1;
}
const varyingPort = portBits.map((b, w) => ({offset: w * 4, bits: b, changed: b.reduce((a, x) => a + x, 0)}))
    .filter(r => r.changed > 0);
console.log(`port offsets that change at all: ${varyingPort.length} of ${words}`);

// The identification, over the whole corpus and over the cases whose opcode carries a measured row.
// Only the rows the title-16 table marks with measured votes are trusted to have the right body; over
// everything else the change shape being compared belongs to whatever body that number happens to hit.
const TRUSTED_OPS = new Set([6, 102, 306, 423, 429, 430]);
const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);
const subset = (bits, keep) => {          // written plainly: the library-free reading of the same slice
    const out = new Uint8Array(keep.length);
    for (let i = 0; i < keep.length; i++) if (keep[i]) out[i] = bits[i];
    return out;
};
// A match inside a scope in which the word barely moves is no match: a comparison has to have at least
// MIN_CHANGES differences in it, or it rests on two zero vectors (section 312.3's own caveat).
const MIN_CHANGES = 2;
const moves = (bits, keep) => subset(bits, keep).reduce((x, y) => x + y, 0);
const keepAll = cases.map(() => true);
const keepTrusted = cases.map(row => TRUSTED_OPS.has(row.op));
const identify = (keep, label) => {
    const rows = [];
    for (const n of varyingNative) {
        const nb = subset(n.bits, keep);
        const found = varyingPort.filter(p => moves(n.bits, keep) >= MIN_CHANGES
            && moves(p.bits, keep) >= MIN_CHANGES && same(nb, subset(p.bits, keep)));
        rows.push({native: `0x${n.offset.toString(16)}`, changedInCases: nb.reduce((a, x) => a + x, 0),
                   candidates: found.map(p => `word+0x${p.offset.toString(16)}`)});
    }
    const mapped = rows.filter(r => r.candidates.length > 0);
    console.log(`scope ${label}: ${keep.filter(Boolean).length} cases, identified ${mapped.length} of ${rows.length},`
        + ` of them unique ${rows.filter(r => r.candidates.length === 1).length}`);
    for (const r of mapped.slice(0, 10))
        console.log(`  ${r.native} changed in ${r.changedInCases} -> ${r.candidates.slice(0, 4).join(', ')}`);
    return rows;
};
const selfCheck = varyingNative.find(v => v.offset === 0x18);
console.log(`self-check: varyingNative 0x18 says ${selfCheck && selfCheck.changed}, its bits ${selfCheck && selfCheck.bits.length}`
    + `, through subset it says ${selfCheck && subset(selfCheck.bits, keepAll).reduce((x, y) => x + y, 0)}`);
const identified = identify(keepAll, 'the whole corpus');
const trusted = identify(keepTrusted, 'the measured rows');
console.log(`still unidentified over the whole corpus: ${identified.filter(r => !r.candidates.length).length}`);
console.log(`still unidentified over the measured rows: ${trusted.filter(r => !r.candidates.length).length}`);

writeFileSync(resolve(doc, 'th16-anm-fingerprint.json'),
    JSON.stringify({corpusCases: cases.length, nativeVarying: identified.length,
                   identified: identified.filter(r => r.candidates.length).length,
                   trustedOps: [...TRUSTED_OPS], trustedCases: keepTrusted.filter(Boolean).length,
                   identifiedInTrustedScope: trusted.filter(r => r.candidates.length).length,
                   entries: identified, trustedEntries: trusted}, null, 2) + '\n', 'utf8');
console.log('wrote docs/porting/th16-anm-fingerprint.json');
