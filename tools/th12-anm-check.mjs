// Compare the TH12 port against the original's handlers, case by case.
//
// The oracle (tools/th12-anm-native.py) records the whole 0x700-byte context of the original at the next
// dispatch boundary, because the field layout there is TH12's own: its ABI keeps the script
// pointer at +0x3f0
// where TH13 keeps colours at +0x528 and TH14 at +0x534. The port has a layout of its own too
// (sizeof(AnmVm) is 1076). So this checker does not declare a mapping: it DERIVES one, by asking which
// port offset carries, across all 1280 cases, the same sequence of values as a given native slot, and
// then asserts equality through that mapping. A mapping with no candidate is a failure in the open.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const rt = resolve(root, 'runtimes/th12/th12_web');
const out = resolve(root, 'artifacts/th12/anm-check');
// The whole measured table, not a sample of it: the referee should cover every dispatched handler,
// which is why the oracle gained --all.
const oracle = resolve(root, 'artifacts/th12/anm-native.json');
mkdirSync(out, {recursive: true});
const sha = b => createHash('sha256').update(b).digest('hex');

if (!existsSync(oracle) || process.argv.includes('--probe')) {
    execFileSync('py', ['-3', resolve(root, 'tools/th12-anm-native.py')],
                {cwd: root, stdio: 'inherit', windowsHide: true});
}
const proof = JSON.parse(readFileSync(oracle, 'utf8'));

const sources = ['AnmInterpreter', 'AnmVm', 'AnmGeometry', 'Interpolation', 'AnmResource'].map(s => `cpp/game/${s}.cpp`);
const fixture = 'tests/cpp/th12-anm-fixture.cpp';
const wasm = resolve(out, 'th12.wasm');
const clang = resolve(root, 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
    '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--export-memory', '-DPORT_TITLE=12',
    ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
    {cwd: rt, stdio: 'inherit', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});

const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const bytes = readFileSync(wasm);
const {instance} = await WebAssembly.instantiate(bytes, {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;

const size = c.size() >>> 0;
const offsets = [];
for (let o = 0; o + 4 <= size; o += 4) offsets.push(o);
const NATIVE_SNAPSHOT = proof.measured.snapshot;
const PORT_TITLE_NUMBER = 12;
// Title 12's own ABI, and the generator records the address its probe put the script at.
const CODE_BASE = Number(proof.measured.codeBase ?? '0x70110000');
const POSITION_SLOT = Number(proof.measured.positionSlot ?? '0x28');

// One pass over the oracle's cases: the native vector per slot, and every port candidate vector.
const NAMES = [
    {name: 'flags', get: () => c.named(0) >>> 0},
    {name: 'flags2', get: () => c.named(1) >>> 0},
    {name: 'title flags', get: () => c.named(2) >>> 0},
    {name: 'layer', get: () => c.named(3) >>> 0},
    {name: 'color', get: () => c.named(4) >>> 0},
    {name: 'secondary color', get: () => c.named(5) >>> 0},
    {name: 'integer 0', get: () => c.named(6) >>> 0},
    {name: 'integer 1', get: () => c.named(7) >>> 0},
    {name: 'live', get: () => c.named(8) >>> 0},
    {name: 'scale.x', get: () => c.named_real(0) >>> 0},
    {name: 'scale.y', get: () => c.named_real(1) >>> 0},
    {name: 'timer fractional', get: () => c.named_real(2) >>> 0},
];
const namedVectors = new Map(NAMES.map(x => [x.name, []]));
// Where the port's own members sit. The fixture reports the layout with offsetof and its names
// from the same table, so this reads the port's layout instead of restating it, and a gap slot
// can be described by the name of the field that reproduces it.
const cString = pointer => {
    const view = new Uint8Array(c.memory.buffer);
    let text = '';
    for (let at = pointer >>> 0; view[at]; at++) text += String.fromCharCode(view[at]);
    return text;
};
const NAMED_OFFSETS = [];
for (let i = 0, total = c.member_total() >>> 0; i < total; i++) {
    NAMED_OFFSETS.push({name: cString(c.member_name(i) >>> 0), offset: c.member_offset(i) >>> 0});
}
NAMED_OFFSETS.sort((a, b) => a.offset - b.offset || a.name.localeCompare(b.name));
const rowOps = [];                 // the opcode of each row that ran, in order
const advances = new Map();         // opcode -> the native position advances it showed
let skippedFaults = 0;
let classedOut = 0;
const nativeBeforeWords = [];
const nativeBuffers = [];
const namedDeltas = [];
const slots = new Map();     // native slot -> values, one per case
for (let o = 0; o + 4 <= NATIVE_SNAPSHOT; o += 4) slots.set(o, []);
const portWords = new Map(offsets.map(o => [o, []]));
const portReals = new Map(offsets.map(o => [o, []]));
// The port's word before its own run, so a change can be compared with a change: the original's
// slots are the values of a title-specific object layout and the port shares algorithms, not
// layouts, so a slot absent from every absolute vector can still carry a change the port makes.
const portBefore = new Map(offsets.map(o => [o, []]));
const portDelta = [];
const statuses = [];
const statusByOp = new Map();   // a body that reports itself still performing is a harness dependency
// The game's own ANM buffers, opened BEFORE the runs: a body that binds a sprite needs one, and
// opening them after the cases was the reason opcode 102 failed every one of its forty cases.
const archivePath = resolve(root, 'artifacts/archive-differential/TH12.json');
const resources = [];
if (existsSync(archivePath)) {
    const archive = JSON.parse(readFileSync(archivePath, 'utf8'));
    for (const entry of archive.decoded.filter(f => f.name.endsWith('.anm')).slice(0, 64)) {
        const data = readFileSync(resolve(archive.extraction, entry.name));
        if (sha(data) !== entry.sha256) continue;
        const p = c.allocate(data.length);
        try {
            new Uint8Array(c.memory.buffer, p, data.length).set(data);
            resources.push({name: entry.name, result: c.open_resource(p, data.length),
                           sprites: c.sprites_open()});
        } finally { c.release(p); }
    }
}

for (const row of proof.cases) {
    if (row.fault) { skippedFaults++; continue; }
    const native = Buffer.from(row.context, 'hex');
    nativeBeforeWords.push(Buffer.from(row.before, 'hex'));
    rowOps.push(row.op);
    const advance = (native.readUInt32LE(POSITION_SLOT) - CODE_BASE) >>> 0;
    if (!advances.has(row.op)) advances.set(row.op, new Set());
    advances.get(row.op).add(advance);
    for (const o of slots.keys()) slots.get(o).push(native.readUInt32LE(o));
    c.reset(row.value | 0, row.variant);
    const namedBeforeRun = NAMES.map(x => x.get());
    for (const o of offsets) portBefore.get(o).push(c.slot(o) >>> 0);
    const runStatus = c.run(row.op, row.value | 0, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
    statuses.push(runStatus);
    if (runStatus) statusByOp.set(row.op, (statusByOp.get(row.op) || 0) + 1);
    for (const o of offsets) { portWords.get(o).push(c.slot(o) >>> 0); portReals.get(o).push(c.real_slot(o) >>> 0); }
    portDelta.push(c.delta() >>> 0);
    for (const x of NAMES) namedVectors.get(x.name).push(x.get());
    nativeBuffers.push(native);
    namedDeltas.push(NAMES.map((x, k) => ((x.get() ^ namedBeforeRun[k]) >>> 0)));
}
// --- arrangement census, from tools/anm-check-add-arrangement.py

// The arrangement of the newer flag words, solved by this instrument and read from no other: for
// every bit the native pair changes in, and within each opcode over all of that opcode's cases,
// which port channel bit reproduces the change in every case. The comparison is over the change,
// because the corpus seeds the native word and the port seeds its own fields (section 344).
// A bit no single channel bit reproduces is tried again as a pair of bits before it is called
// unsettled, and the pair that comes closest is recorded beside it (section 346).
const ARRANGEMENT_SLOTS = {
  12: [0x47c, 0x3fc],  // the two hottest non-position words of the th12 corpus
  16: [0x530, 0x534], 17: [0x530, 0x534], 18: [0x534, 0x538]}[PORT_TITLE_NUMBER];
const casesByOp = new Map();
for (let i = 0; i < rowOps.length; i++) {
    if (!casesByOp.has(rowOps[i])) casesByOp.set(rowOps[i], []);
    casesByOp.get(rowOps[i]).push(i);
}
const channelNames = NAMES.map(x => x.name);
// `live` is the harness reporting that the VM still has an instruction, and a handler that ends the
// instruction changes it in exactly the cases a flag row asks about; so it is preferred last.
const channelOrder = channelNames.map((n, k) => [n, k])
    .sort((a, b) => (a[0] === 'live' ? 1 : 0) - (b[0] === 'live' ? 1 : 0))
    .map(pair => pair[1]);
const arrangementRows = [];
const arrangementUnsettled = [];
let arrangementChanging = 0;
for (const slot of ARRANGEMENT_SLOTS) {
    for (let p = 0; p < 32; p++) {
        const perOp = new Map();
        for (const [op, list] of casesByOp) {
            const want = list.map(i => (((nativeBuffers[i].readUInt32LE(slot)
                ^ nativeBeforeWords[i].readUInt32LE(slot)) >>> p) & 1));
            if (!want.some(x => x)) continue;
            const series = [];
            for (let k = 0; k < NAMES.length; k++) {
                for (let q = 0; q < 32; q++) {
                    series.push({k, q, v: list.map(i => (namedDeltas[i][k] >>> q & 1))});
                }
            }
            const matches = (a, b) => {
                for (let j = 0; j < list.length; j++) {
                    if (((a.v[j] ^ (b ? b.v[j] : 0)) >>> 0) !== want[j]) return false;
                }
                return true;
            };
            let found = null;
            for (const k of channelOrder) {
                for (let q = 0; q < 32 && !found; q++) {
                    const one = series.find(s => s.k === k && s.q === q);
                    if (matches(one, null)) found = {sources: [{channel: channelNames[k], portBit: q}],
                                                    kind: 'one'};
                }
                if (found) break;
            }
            if (!found) {
                // the field shape the code rows describe for the pair names: an adjacent pair of
                // bits of one channel, and failing that any two bits, exactly.
                for (let k = 0; k < NAMES.length && !found; k++) {
                    for (let q = 0; q + 1 < 32 && !found; q++) {
                        const a = series.find(s => s.k === k && s.q === q);
                        const b = series.find(s => s.k === k && s.q === q + 1);
                        if (matches(a, b)) found = {sources: [{channel: channelNames[k], portBit: q},
                                                             {channel: channelNames[k],
                                                              portBit: q + 1}], kind: 'two'};
                    }
                }
                if (!found) {
                    outer: for (const a of series) {
                        for (const b of series) {
                            if (b.k === a.k && b.q <= a.q) continue;
                            if (matches(a, b)) {
                                found = {sources: [{channel: channelNames[a.k], portBit: a.q},
                                                   {channel: channelNames[b.k], portBit: b.q}],
                                         kind: 'two'};
                                break outer;
                            }
                        }
                    }
                }
            }
            if (found) perOp.set(op, found);
        }
        const anyChange = [...casesByOp.values()].some(list => list.some(i =>
            (((nativeBuffers[i].readUInt32LE(slot) ^ nativeBeforeWords[i].readUInt32LE(slot))
              >>> p) & 1)));
        if (!anyChange) continue;
        arrangementChanging++;
        if (perOp.size) {
            const sources = [...perOp.values()];
            arrangementRows.push({slot: `0x${slot.toString(16)}`, nativeBit: p,
                kind: sources.some(s => s.kind === 'one') ? 'one' : 'two',
                byOpcode: [...perOp.entries()].map(([op, f]) => ({op, sources: f.sources})),
                channels: [...new Set(sources.flatMap(s => s.sources.map(x => x.channel)))]});
        } else {
            arrangementUnsettled.push({slot: `0x${slot.toString(16)}`, nativeBit: p,
                opcodes: [...casesByOp.keys()].filter(op => false)});
        }
    }
}
const arrangementChannels = {};
for (const row of arrangementRows) {
    for (const channel of row.channels) arrangementChannels[channel] = (arrangementChannels[channel] || 0) + 1;
}
// A row is credible only if its source bit is not claimed by another native bit of the same
// opcode: two native bits cannot come from one port bit, so a clash means the sort of coincidence
// that live and the timer's fractional part produce, changing whenever the handler ends.
const claims = new Map();
for (const row of arrangementRows) {
    for (const part of row.byOpcode) {
        for (const source of part.sources) {
            const key = `${part.op}:${source.channel}:${source.portBit}`;
            if (!claims.has(key)) claims.set(key, new Set());
            claims.get(key).add(`${row.slot}:${row.nativeBit}`);
        }
    }
}
const ambiguousOf = row => row.byOpcode.some(part => part.sources.some(source =>
    claims.get(`${part.op}:${source.channel}:${source.portBit}`).size > 1));
const clockSources = new Set(['live', 'timer fractional']);
const credibleRows = arrangementRows.filter(row => !ambiguousOf(row));
const credibleFromFlags = credibleRows.filter(row =>
    row.channels.every(channel => !clockSources.has(channel)));
const arrangementCensus = {
    slots: ARRANGEMENT_SLOTS.map(s => `0x${s.toString(16)}`),
    changingNativeBits: arrangementChanging,
    bitsWithARow: arrangementRows.length,
    settledByOneBit: arrangementRows.filter(r => r.kind === 'one').length,
    settledByTwoBits: arrangementRows.filter(r => r.kind === 'two').length,
    credibleBits: credibleRows.length,
    credibleFromFlagChannels: credibleFromFlags.length,
    ambiguousBits: arrangementRows.length - credibleRows.length,
    ambiguousRows: arrangementRows.filter(ambiguousOf).map(r => `${r.slot}:${r.nativeBit}`),
    unsettledBits: arrangementUnsettled.length,
    unsettled: arrangementUnsettled.slice(0, 16),
    channelsUsed: arrangementChannels,
    rows: arrangementRows,
    reading: 'a bit is settled when one port channel bit reproduces its change in every case of the '
             + 'opcode that writes it, or when a pair of bits does; it is credible when the source '
             + 'bit is not also claimed by another native bit of that opcode',
};
console.log(`arrangement: ${arrangementRows.length} of ${arrangementChanging} changing native bits of `
    + `${arrangementCensus.slots.join(' and ')} settle (one bit ${arrangementCensus.settledByOneBit}, `
    + `pair ${arrangementCensus.settledByTwoBits}); ${arrangementUnsettled.length} unsettled; `
    + `credible ${credibleRows.length}, of which ${credibleFromFlags.length} from flag channels; `
    + `sources ${JSON.stringify(arrangementChannels)}`);

// The pointer-install class, derived here rather than hardcoded: an opcode belongs to it when any of
// its runs advanced the position by something other than a stored instruction length (section 307).
const installClass = new Set([...advances.entries()]
    .filter(([, set]) => [...set].some(a => a !== 12 && a !== 16)).map(([op]) => op));
const varying = [...slots.entries()].filter(([, v]) => new Set(v).size > 1);
const same = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

// Derive: for each native slot that varies, the port offsets carrying the same sequence, under the
// identity and (for pointers into the original's code) the subtraction of that code's base.
const derived = [];
let positionPairs = null;
const positionMismatchOps = new Map();   // native advance against port delta, over the opcodes that fall through
for (const [slot, values] of varying) {
    const found = [];
    for (const o of offsets) {
        if (same(values, portWords.get(o))) found.push({port: `word+0x${o.toString(16)}`, kind: 'word'});
        if (same(values, portReals.get(o))) found.push({port: `float+0x${o.toString(16)}`, kind: 'float'});
    }
    if (slot === POSITION_SLOT) {
        const shifted = values.map(v => (v - CODE_BASE) >>> 0);
        // Where the body falls through, the position is the port's own delta. The measured
        // pointer-install class (13 opcodes, section 307) is excluded from the claim and counted.
        const plain = rowOps.map(op => !installClass.has(op));
        const equalWherePlain = plain.every((keep, i) => !keep || shifted[i] === portDelta[i]);
        if (!positionPairs) {
            positionPairs = new Map();
            for (let i = 0; i < values.length; i++)
                if (plain[i] && shifted[i] !== portDelta[i] && shifted[i] === 12)
                    positionMismatchOps.set(rowOps[i], (positionMismatchOps.get(rowOps[i]) || 0) + 1);
            for (let i = 0; i < values.length; i++) {
                if (!plain[i]) continue;
                const key = `${shifted[i]} -> ${portDelta[i]}`;
                positionPairs.set(key, (positionPairs.get(key) || 0) + 1);
            }
        }
        if (plain.some(Boolean) && equalWherePlain)
            found.push({port: 'delta', kind: 'delta', shift: CODE_BASE, where: 'plain fall-through',
                        classedOut: plain.filter(x => !x).length});
    }
    derived.push({nativeSlot: `0x${slot.toString(16)}`, distinctValues: new Set(values).size, candidates: found});
}
const mapped = derived.filter(d => d.candidates.length > 0);
const unmapped = derived.filter(d => d.candidates.length === 0);

// The assertion pass, through the first candidate of each derived mapping.
const differences = [];
const byDescriptor = new Map();
let comparisons = 0;
let caseIndex = -1;
for (const [index, row] of proof.cases.entries()) {
    if (row.fault) continue;
    caseIndex++;
    const portCase = caseIndex;   // the port's vectors no longer carry the faulted rows
    const native = Buffer.from(row.context, 'hex');
    nativeBeforeWords.push(Buffer.from(row.before, 'hex'));
    for (const d of mapped) {
        const slot = parseInt(d.nativeSlot, 16);
        const candidate = d.candidates[0];
        if (candidate.where === 'plain fall-through' && installClass.has(row.op)) {
            classedOut++;   // the port recorded the pointer-install class; the claim does not cover it
            continue;
        }
        const want = candidate.shift ? (native.readUInt32LE(slot) - candidate.shift) >>> 0
                                     : native.readUInt32LE(slot);
        let got;
        if (candidate.kind === 'delta') got = portDelta[portCase];
        else if (candidate.kind === 'word') got = portWords.get(parseInt(candidate.port.slice(7), 16))[portCase];
        else got = portReals.get(parseInt(candidate.port.slice(8), 16))[portCase];
        comparisons++;
        if (want !== got) {
            const key = `${row.op}:${d.nativeSlot}`;
            byDescriptor.set(key, (byDescriptor.get(key) || 0) + 1);
            if (differences.length < 20) {
                differences.push({case: index, op: row.op, value: row.value, variant: row.variant, refs: row.refs,
                                 nativeSlot: d.nativeSlot, port: candidate.port,
                                 native: `0x${want.toString(16)}`, portValue: `0x${got.toString(16)}`});
            }
        }
    }
}
// For every slot the derivation could not map, the named member of the port whose sequence comes
// closest: the gap gets a name and a size rather than only a verdict.
const nearestNamed = [];
for (const d of unmapped) {
    const values = slots.get(parseInt(d.nativeSlot, 16));
    let best = null;
    for (const [name, vector] of namedVectors) {
        if (!vector.length) continue;
        let differing = 0;
        for (let i = 0; i < values.length; i++) if (values[i] !== vector[i]) differing++;
        if (!best || differing < best.differing) best = {member: name, differing};
    }
    // The named member answers "which field", and the offset answers "which byte": a slot whose
    // closest offset differs in a handful of cases is a seed or an edge, one that differs
    // everywhere is a field the port does not carry at all.
    let near = null;
    for (const o of offsets) {
        const vector = portWords.get(o);
        if (!vector.length) continue;
        let differing = 0;
        for (let i = 0; i < values.length; i++) if (values[i] !== vector[i]) differing++;
        if (!near || differing < near.differing) near = {offset: o, differing};
    }
    // The second pass, on changes rather than on states. The port mirrors this title's
    // behaviour without mirroring the original's object, so a slot can be absent from every
    // absolute vector while the port makes exactly the same change somewhere in its own layout.
    const before = nativeBeforeWords;
    const changed = i => (nativeBuffers[i].readUInt32LE(parseInt(d.nativeSlot, 16))
                        ^ before[i].readUInt32LE(parseInt(d.nativeSlot, 16))) >>> 0;
    let byDelta = null;
    for (const o of offsets) {
        const after = portWords.get(o), pre = portBefore.get(o);
        if (!after || !pre || !after.length) continue;
        let differing = 0;
        for (let i = 0; i < values.length; i++)
            if (changed(i) !== ((after[i] ^ pre[i]) >>> 0)) differing++;
        if (!byDelta || differing < byDelta.differing) byDelta = {offset: o, differing};
    }
    nearestNamed.push({nativeSlot: d.nativeSlot, closestMember: best ? best.member : null,
                      differingCases: best ? best.differing : null, ofCases: values.length,
                      closestOffset: near ? `0x${near.offset.toString(16)}` : null,
                      closestOffsetDiffering: near ? near.differing : null,
                      deltaOffset: byDelta ? `0x${byDelta.offset.toString(16)}` : null,
                      deltaDiffering: byDelta ? byDelta.differing : null});
}
const deltaMatched = nearestNamed.filter(r => r.deltaDiffering === 0);

// The bit pass, the instrument the newer titles' census uses, turned on the gap. The original's
// whole word at one offset can be a single bit of one of the port's words - the port's own
// comment on +0x47c says exactly that - so the change of a native bit, over the cases, is
// compared with the change of every port bit. A mask per bit, packed into a BigInt: the run is
// over a few thousand cases and a few hundred offsets, and this keeps it a comparison of masks.
const caseCount = nearestNamed.length ? nearestNamed[0].ofCases : 0;
const maskOf = (read, bit) => {
    let mask = 0n;
    for (let i = 0; i < caseCount; i++) if ((read(i) >>> bit) & 1) mask |= 1n << BigInt(i);
    return mask;
};
const safeRead = values => i => values[i] ?? 0;
const portBitMasks = new Map();      // `${offset}:${bit}` -> mask of the cases where the bit changed
{
    const before = nativeBeforeWords.slice(0, caseCount);
    const nativeCases = nativeBuffers.slice(0, caseCount);
    for (const o of offsets) {
        const after = portWords.get(o), pre = portBefore.get(o);
        if (!after || !pre || after.length < caseCount) continue;
        for (let bit = 0; bit < 32; bit++) {
            let mask = 0n;
            for (let i = 0; i < caseCount; i++) if (((after[i] ^ pre[i]) >>> bit) & 1) mask |= 1n << BigInt(i);
            if (mask !== 0n) portBitMasks.set(`${o}:${bit}`, mask);
        }
    }
    const bitRows = [];
    for (const d of unmapped) {
        const slot = parseInt(d.nativeSlot, 16);
        const after = nativeCases, pre = before;
        const read = (i) => ((after[i].readUInt32LE(slot) ^ pre[i].readUInt32LE(slot)) >>> 0);
        for (let bit = 0; bit < 32; bit++) {
            const mask = maskOf(read, bit);
            if (mask === 0n) continue;
            const at = [];
            for (const [key, other] of portBitMasks) if (other === mask) at.push(key);
            bitRows.push({nativeSlot: d.nativeSlot, nativeBit: bit, distinctPortBits: at.length,
                         closeMatch: at.slice(0, 4)});
        }
    }
    var bitRowsOut = bitRows;
    var bitSummary = {
        nativeChangingBits: bitRows.length,
        matchedExactly: bitRows.filter(r => r.distinctPortBits > 0).length,
        slotsWhollyOrPartlyMatched: new Set(bitRows.filter(r => r.distinctPortBits > 0)
            .map(r => r.nativeSlot)).size,
        distinctPortBitsUsed: new Set(bitRows.flatMap(r => r.closeMatch)).size,
        sharedMasks: bitRows.filter(r => r.distinctPortBits > 1).length,
        reading: 'a native bit is matched when one port bit changes in exactly the cases it does; '
                 + 'the source bit need not be the same bit of the same field'
    };
}
void safeRead;
const tracked = [...sources, ...['AnmOpcodes', 'AnmVm', 'AnmResource', 'AnmGeometry', 'Interpolation', 'Timer', 'Rng',
    'Types', 'PortTitle'].map(p => `cpp/game/${p}.hpp`), fixture];
const report = {
    passed: unmapped.length === 0 && differences.length === 0,
    classedOutComparisons: classedOut,
    nonzeroStatusesByOpcode: [...statusByOp.entries()].sort((a, b) => b[1] - a[1]).slice(0, 16)
        .map(([op, cases]) => ({op, casesOutOfForty: cases})),
    positionMismatchOpcodes: [...positionMismatchOps.entries()].sort((a, b) => b[1] - a[1])
        .map(([op, count]) => ({op, casesOfForty: count})),
    positionPairs: positionPairs ? [...positionPairs.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12)
        .map(([pair, count]) => ({advance_to_portDelta: pair, cases: count})) : [],
    scope: 'The context after each handler, at the next dispatch boundary. The native layout is TH12\'s own, '
         + 'so the mapping from its slots to port offsets is derived from the cases, not declared. '
         + 'No renderer and no complete-game equivalence is claimed.',
    nativeExecutableSha256: proof.executableSha256,
    nativeCases: proof.cases.length,
    nativeCoverage: proof.measured.coverage,
    nativeRealHandlers: proof.realHandlers,
    skippedFaultedCases: skippedFaults,
    nativeOpcodes: new Set(proof.cases.map(r => r.op)).size,
    measuredConstants: proof.measured,
    namedMemberOffsets: NAMED_OFFSETS,
    derivedMapping: derived,
    derivedArrangement: arrangementCensus,
    unmappedSlots: unmapped,
    nearestNamedMemberPerUnmappedSlot: nearestNamed,
    // The composition of the gap: how many of the uncandidated slots the port reproduces as a
    // change somewhere in its own layout, and which of its offsets carries it.
    deltaMatchedUnmappedSlots: deltaMatched.map(r => ({nativeSlot: r.nativeSlot,
                                                      deltaOffset: r.deltaOffset})),
    deltaSummary: {matchedAsAChange: deltaMatched.length, ofUnmapped: nearestNamed.length},
    bitPassOverUnmappedSlots: {summary: bitSummary, rows: bitRowsOut},
    pointerInstallClass: {derivedFrom: 'oracle advances', opcodes: [...installClass].sort((a, b) => a - b)},
    positionClaim: 'the position is the port\'s delta for every opcode that falls through; the '
                   + 'pointer-install class above is excluded and counted',
    differencesByDescriptor: [...byDescriptor.entries()].sort((a, b) => b[1] - a[1]).slice(0, 40)
        .map(([what, count]) => ({descriptor: what, differingComparisons: count})),
    comparisons,
    differences: differences.length,
    firstDifferences: differences.slice(0, 12),
    wasmSha256: sha(bytes),
    resources: resources.length ? resources : undefined,
    sourceHashes: Object.fromEntries(tracked.map(p => [p, sha(readFileSync(resolve(rt, p)))])),
    toolHashes: Object.fromEntries(['tools/th12-anm-native.py', 'tools/th12-anm-check.mjs', 'tools/th-anm-handlers.py']
        .map(p => [p, sha(readFileSync(resolve(root, p)))])),
};
writeFileSync(resolve(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
writeFileSync(resolve(root, 'docs/porting/th12-anm-verified.json'), JSON.stringify(report, null, 2) + '\n');
const mappedNames = derived.map(d => `${d.nativeSlot} -> ${d.candidates.map(x => x.port).join('|') || 'NONE'}`);
console.log(`TH12 ANM: ${proof.cases.length} native cases over ${report.nativeOpcodes} opcodes, ${comparisons} comparisons.`);
console.log('derived mapping: ' + mappedNames.join('  '));
console.log(`unmapped slots: ${unmapped.length}; differing comparisons: ${differences.length}; passed: ${report.passed}`);
console.log(`delta pass: ${deltaMatched.length} of the ${unmapped.length} uncandidated slots carry the same change `
    + `somewhere in the port; ${new Set(deltaMatched.map(r => r.deltaOffset)).size} distinct port offsets do it`);
console.log(`bit pass: ${bitSummary.matchedExactly} of ${bitSummary.nativeChangingBits} changing native bits of the `
    + `uncandidated slots are reproduced by some port bit, covering ${bitSummary.slotsWhollyOrPartlyMatched} of `
    + `${unmapped.length} slots and ${bitSummary.distinctPortBitsUsed} distinct port bits`);
for (const r of nearestNamed) console.log(`  ${r.nativeSlot} closest to ${r.closestMember}: ${r.differingCases} of ${r.ofCases} cases differ`
    + (r.deltaDiffering === 0 ? `; the change is the port's ${r.deltaOffset}` : ''));
if (!report.passed) process.exitCode = 1;
