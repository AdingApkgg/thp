// Search for the channel the newer titles' flag word is a shift of.
//
// The checker of section 340 derives the native-to-port mapping by equality of whole words, and the
// newer flag word has no candidate under equality: the port keeps those flags in bits of a word it
// already has, and the native word holds the same bits at other positions - the comments of
// `AnmOpcodes.hpp` name the relation for the ones that were measured ("slot 0x534 bit 7, and its
// mask 0x80 is one below the flag6 home at flags2 bit 6"). Equality of whole words cannot see a
// shift, so this probe looks for one: for each named port channel and each of the 32 shifts, count
// the cases in which the rotated channel matches the native word under the mask the native values
// themselves determine. A channel and shift matching in every case is the channel; a best count
// short of that is the residual, in cases.
//
// Usage: node tools/anm-arrangement-search.mjs --title=16 [--slots=0x530,0x534]
import {readFileSync, existsSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {WASI} from 'node:wasi';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const title = Number((process.argv.find(a => a.startsWith('--title=')) || '--title=16').split('=')[1]);
const wanted = ((process.argv.find(a => a.startsWith('--slots=')) || '--slots=0x530,0x534')
    .split('=')[1]).split(',').map(s => parseInt(s, 16));
const wasm = resolve(root, `artifacts/th${title}/anm-check/th${title}.wasm`);
const oracle = resolve(root, `artifacts/th${title}/` +
    (title === 16 ? 'anm-native-all.json' : 'anm-native.json'));
if (!existsSync(wasm)) { console.log(`  no build at ${wasm}`); process.exit(0); }
const proof = JSON.parse(readFileSync(oracle, 'utf8'));

const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync(wasm), {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const offsets = [];
for (let o = 0; o + 4 <= (c.size() >>> 0); o += 4) offsets.push(o);

const archivePath = resolve(root, `artifacts/archive-differential/th${title}.json`);
if (existsSync(archivePath)) {
    const archive = JSON.parse(readFileSync(archivePath, 'utf8'));
    for (const entry of archive.decoded.filter(f => f.name.endsWith('.anm')).slice(0, 64)) {
        const data = readFileSync(resolve(archive.extraction, entry.name));
        const p = c.allocate(data.length);
        try {
            new Uint8Array(c.memory.buffer, p, data.length).set(data);
            c.open_resource(p, data.length);
        } finally { c.release(p); }
    }
}

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
];
const native = new Map(wanted.map(s => [s, []]));
const channels = new Map(NAMES.map(x => [x.name, []]));
for (const row of proof.cases) {
    if (row.fault) continue;
    const n = Buffer.from(row.context, 'hex');
    for (const s of wanted) native.get(s).push(n.readUInt32LE(s));
    c.run(row.op, row.value | 0, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
    for (const x of NAMES) channels.get(x.name).push(x.get());
}
if (process.argv.includes('--residual')) {
    // The nearest named member is not the word: the corpus seeds the flag word, so the seed's bits
    // match and what is left is the cases whose handler writes with an argument. If that residual is
    // exactly the names the row tables of section 331 measured, then the remaining work has a list.
    const rows = JSON.parse(readFileSync(resolve(root, 'docs/porting/anm-flag-rows-16-18.json'),
                                        'utf8'));
    const measured = Object.keys(rows.titles[String(title)].rows).map(Number).sort((a, b) => a - b);
    for (const s of wanted) {
        const values = native.get(s);
        const key = NAMES.map(x => x.name).find(n => n === 'title flags');
        const vector = channels.get(key);
        const byOp = new Map();
        let differ = 0;
        let index = 0;
        for (const row of proof.cases) {
            if (row.fault) continue;
            const mine = vector[index++];
            if (((mine & values[index - 1]) >>> 0) === values[index - 1]) continue;
            differ++;
            byOp.set(row.op, (byOp.get(row.op) || 0) + 1);
        }
        console.log(`  native 0x${s.toString(16)} against the port's ${key}: ${differ} of ` +
            `${values.length} cases differ`);
        const ops = [...byOp.keys()].sort((a, b) => a - b);
        console.log(`     differing opcodes: ${ops.join(', ')}`);
        console.log(`     measured by the row tables: ${measured.join(', ')}`);
        console.log(`     the residual is inside the measured names: ` +
            `${ops.every(op => measured.includes(op))}`);
    }
    process.exit(0);
}
if (process.argv.includes('--delta')) {
    // Absolute values carry the fixture's seed; what a case MEANS is what it changes. This mode
    // resets, reads, steps and reads again - the fixture was built with those two exports for exactly
    // this - so every port offset has a delta per case, and so has the native slot, from the
    // corpus's before and context. Per native bit that ever changes, it then names the port bit
    // that changed with it in the most cases, which is the bit the port would have to route.
    const pairVotes = new Map();       // `${slot}:${bit}` -> Map(`${off}:${bit}` -> hits)
    const changedCases = new WeakMap();
    const carry = [];
    for (const row of proof.cases) {
        if (row.fault) continue;
        const b = Buffer.from(row.before, 'hex');
        const a = Buffer.from(row.context, 'hex');
        const ro = c.reset(row.value | 0, row.variant);
        const beforeWords = offsets.map(o => c.slot(o) >>> 0);
        const beforeNamed = NAMES.map(x => x.get());
        c.step(row.op, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
        const afterWords = offsets.map(o => c.slot(o) >>> 0);
        const afterNamed = NAMES.map(x => x.get());
        carry.push({row, b, a, dWords: afterWords.map((v, i) => (v ^ beforeWords[i]) >>> 0),
                   dNamed: afterNamed.map((v, i) => (v ^ beforeNamed[i]) >>> 0), ro});
    }
    for (const s of wanted) {
        for (const {row, b, a, dWords, dNamed} of carry) {
            const nd = (a.readUInt32LE(s) ^ b.readUInt32LE(s)) >>> 0;
            for (let p = 0; p < 32; p++) {
                if (!((nd >>> p) & 1)) continue;
                const key = `${s}:${p}`;
                if (!pairVotes.has(key)) pairVotes.set(key, new Map());
                const votes = pairVotes.get(key);
                for (let i = 0; i < offsets.length; i++) {
                    const d = dWords[i];
                    for (let q = 0; q < 32; q++) {
                        if (!((d >>> q) & 1)) continue;
                        const k = `${offsets[i]}:${q}`;
                        votes.set(k, (votes.get(k) || 0) + 1);
                    }
                }
                for (let k = 0; k < dNamed.length; k++) {
                    for (let q = 0; q < 32; q++) {
                        if (!((dNamed[k] >>> q) & 1)) continue;
                        const kk = `${NAMES[k].name}:${q}`;
                        votes.set(kk, (votes.get(kk) || 0) + 1);
                    }
                }
            }
        }
    }
    for (const s of wanted) {
        console.log(`  native 0x${s.toString(16)}: the port bit that changes with each native bit`);
        for (const {row, b, a} of carry) { /* count only, see below */ break; }
        for (let p = 0; p < 32; p++) {
            const votes = pairVotes.get(`${s}:${p}`);
            if (!votes) continue;
            let total = 0;
            for (const {row, b, a} of carry) {
                if ((a.readUInt32LE(s) ^ b.readUInt32LE(s)) >>> p & 1) total++;
            }
            const best = [...votes.entries()].sort((x, y) => y[1] - x[1]).slice(0, 3);
            console.log(`     native bit ${String(p).padStart(2)} changes in ${String(total).padStart(4)}` +
                ` cases -> ${best.map(([k, n]) => `${k} ${n}`).join(', ') || 'no port bit changed'}`);
        }
    }
    process.exit(0);
}
const rowNativeCache = [];
if (process.argv.includes('--solve')) {
    // Co-change is not attribution: one case can change three port bits and one native bit, and then
    // all three co-change with it. This mode treats the cases as vectors over GF(2) and asks the
    // exact question - which XOR of port bits reproduces the native bit in EVERY case - trying the
    // smallest sets first.
    const names = [];
    const vectors = [];
    const bits = [];
    const solveRows = proof.cases.filter(r => {
        const only = (process.argv.find(a => a.startsWith('--op=')) || '').split('=')[1];
        return !only || only.split(',').map(Number).includes(r.op);
    });
    if (process.argv.some(a => a.startsWith('--op='))) {
        console.log(`  ${solveRows.length} cases of the opcodes named`);
    }
    for (const row of solveRows) {
        if (row.fault) continue;
        const b = Buffer.from(row.before, 'hex');
        bits.push(ROW => ROW);
        void bits;
        const a = Buffer.from(row.context, 'hex');
        c.reset(row.value | 0, row.variant);
        const beforeWords = offsets.map(o => c.slot(o) >>> 0);
        const beforeNamed = NAMES.map(x => x.get());
        if (process.argv.includes('--via-run')) {
            c.run(row.op, row.value | 0, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
        } else {
            c.step(row.op, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
        }
        const afterWords = offsets.map(o => c.slot(o) >>> 0);
        const afterNamed = NAMES.map(x => x.get());
        const rowNative = wanted.map(s => (a.readUInt32LE(s) ^ b.readUInt32LE(s)) >>> 0);
        for (const x of NAMES) void x;
        vectors.push({words: afterWords.map((v, i) => (v ^ beforeWords[i]) >>> 0),
                     named: afterNamed.map((v, i) => (v ^ beforeNamed[i]) >>> 0)});
        for (const s of wanted) void s;
        names.push(null);
        rowNativeCache.push(rowNative);
    }
    // label every port bit by (source, bit); the source list is the named set first, since the
    // port keeps its fields there, then the raw offsets.
    const labels = [];
    const series = [];
    const push = (label, get) => {
        labels.push(label);
        series.push(vectors.map(v => get(v)));
    };
    for (let k = 0; k < NAMES.length; k++) {
        for (let q = 0; q < 32; q++) push(`${NAMES[k].name}:${q}`, v => (v.named[k] >>> q) & 1);
    }
    for (let i = 0; i < offsets.length; i++) {
        for (let q = 0; q < 32; q++) {
            push(`0x${offsets[i].toString(16)}:${q}`, v => (v.words[i] >>> q) & 1);
        }
    }
    const N = series.length;
    const live = [];
    for (let j = 0; j < N; j++) if (series[j].some(x => x)) live.push(j);
    const xorAll = (set) => {
        const out = new Uint8Array(vectors.length);
        for (const j of set) {
            const v = series[j];
            for (let i = 0; i < out.length; i++) out[i] ^= v[i];
        }
        return out;
    };
    for (let t = 0; t < wanted.length; t++) {
        const slot = wanted[t];
        const target = vectors.map((v, i) => (rowNativeCache[i][t] >>> 0));
        const nativeLive = target.filter(v => v).length;
        let portLive = 0;
        for (const v of vectors) if (v.words.some(x => x) || v.named.some(x => x)) portLive++;
        console.log(`  native 0x${slot.toString(16)}: ${nativeLive} of ${target.length} cases change ` +
            `it, and ${portLive} cases change some port bit`);
        if (process.argv.includes('--brief')) continue;
        const bitOf = (value, bit) => ((value >>> bit) & 1);
        console.log(`  native 0x${slot.toString(16)}:`);
        for (let p = 0; p < 32; p++) {
            const want = target.map(v => bitOf(v, p));
            if (!want.some(x => x)) continue;
            let found = null;
            const ranked = live.map(j => {
                let hits = 0;
                for (let i = 0; i < want.length; i++) if (series[j][i] === want[i]) hits++;
                return {j, hits};
            }).sort((x, y) => y.hits - x.hits);
            const pool = ranked.slice(0, 40).map(x => x.j);
            const combos = [];
            for (const a of pool) combos.push([a]);
            for (const a of pool) for (const b2 of pool) if (b2 > a) combos.push([a, b2]);
            for (const a of pool.slice(0, 16)) for (const b2 of pool) for (const d of pool)
                if (b2 > a && d > b2) combos.push([a, b2, d]);
            for (const set of combos) {
                const got = xorAll(set);
                let ok = true;
                for (let i = 0; i < want.length; i++) if (got[i] !== want[i]) { ok = false; break; }
                if (ok) { found = set; break; }
            }
            const text = found ? found.map(j => labels[j]).join(' ^ ') : 'NO EXACT COMBINATION';
            console.log(`     native bit ${String(p).padStart(2)} (${want.filter(Boolean).length} ` +
                `cases) <- ${text}`);
        }
    }
    process.exit(0);
}
if (process.argv.includes('--rule')) {
    // A per-name table would beg the question; a rule can be wrong, so the derivation can catch it.
    // For every shift, ask in how many cases one named port channel moved left by that shift equals the
    // native word inside the mask the native values themselves set.
    for (const s of wanted) {
        const values = native.get(s);
        const union = values.reduce((a, v) => a | v, 0) >>> 0;
        console.log(`  native 0x${s.toString(16)} (union 0x${union.toString(16)}) against a ` +
            `shifted named channel`);
        const ranked = [];
        for (const x of NAMES) {
            const vector = channels.get(x.name);
            for (let shift = 0; shift < 32; shift++) {
                let hits = 0;
                let extra = 0;
                for (let i = 0; i < values.length; i++) {
                    const cand = (((vector[i] << shift) >>> 0) & union) >>> 0;
                    const want = (values[i] & union) >>> 0;
                    if (cand === want) hits++;
                    extra += popcount((cand ^ want) >>> 0);
                }
                if (hits > values.length * 0.8) ranked.push({channel: x.name, shift, hits, extra});
            }
        }
        ranked.sort((a, b) => (b.hits - a.hits) || (a.extra - b.extra));
        for (const row of ranked.slice(0, 5)) {
            console.log(`     ${row.channel} << ${row.shift}: ${row.hits} of ${values.length} ` +
                `cases equal, ${row.extra} differing bits in total` +
                (row.hits === values.length ? '   EQUAL IN EVERY CASE' : ''));
        }
        if (!ranked.length) console.log('     no shift reaches eight cases in ten');
    }
    process.exit(0);
}
if (process.argv.includes('--table')) {
    // The arrangement is per name, so the only complete description of it is a row per name. This
    // walks the corpus's own opcodes and solves each one against the port, printing one line per
    // name with the rows it found - the values-side table the code-side tables can be held against.
    const byOp = new Map();
    for (const row of proof.cases) {
        if (row.fault) continue;
        if (!byOp.has(row.op)) byOp.set(row.op, []);
        byOp.get(row.op).push(row);
    }
    const FLAT = [...NAMES.keys()].map(k => k);
    let solved = 0, total = 0;
    for (const op of [...byOp.keys()].sort((a, b) => a - b)) {
        const list = byOp.get(op);
        const vectors = [];
        const nativeDeltas = wanted.map(() => []);
        for (const row of list) {
            const b = Buffer.from(row.before, 'hex');
            const a = Buffer.from(row.context, 'hex');
            c.reset(row.value | 0, row.variant);
            const before = offsets.map(o => c.slot(o) >>> 0);
            const beforeNamed = NAMES.map(x => x.get());
            c.run(row.op, row.value | 0, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
            const after = offsets.map(o => c.slot(o) >>> 0);
            const afterNamed = NAMES.map(x => x.get());
            vectors.push({words: after.map((v, i) => (v ^ before[i]) >>> 0),
                         named: afterNamed.map((v, i) => (v ^ beforeNamed[i]) >>> 0)});
            wanted.forEach((s, t) => nativeDeltas[t].push(
                (a.readUInt32LE(s) ^ b.readUInt32LE(s)) >>> 0));
        }
        const labels = [];
        const series = [];
        FLAT.forEach((k) => {
            for (let q = 0; q < 32; q++) {
                labels.push(`${NAMES[k].name}:${q}`);
                series.push(vectors.map(v => (v.named[k] >>> q) & 1));
            }
        });
        const mine = offsets.map((o, i) => {
            const out = [];
            for (let q = 0; q < 32; q++) {
                labels.push(`0x${o.toString(16)}:${q}`);
                series.push(vectors.map(v => (v.words[i] >>> q) & 1));
                out.push(series.length - 1);
            }
            return out;
        });
        const rows = [];
        wanted.forEach((slot, t) => {
            const deltas = nativeDeltas[t];
            for (let p = 0; p < 32; p++) {
                const want = deltas.map(v => (v >>> p) & 1);
                if (!want.some(x => x)) continue;
                total++;
                let found = null;
                const ranked = series.map((v, j) => {
                    let hits = 0;
                    for (let i = 0; i < want.length; i++) if (v[i] === want[i]) hits++;
                    return {j, hits};
                }).filter(x => x.hits).sort((x, y) => y.hits - x.hits).slice(0, 24);
                for (const a of ranked) {
                    let ok = true;
                    for (let i = 0; i < want.length; i++)
                        if (series[a.j][i] !== want[i]) { ok = false; break; }
                    if (ok) { found = [a.j]; break; }
                }
                if (!found) {
                    for (const a of ranked) for (const b2 of ranked) {
                        if (b2.j <= a.j) continue;
                        let ok = true;
                        for (let i = 0; i < want.length; i++)
                            if ((series[a.j][i] ^ series[b2.j][i]) !== want[i]) { ok = false; break; }
                        if (ok) { found = [a.j, b2.j]; break; }
                        }
                    }
                if (found) {
                    solved++;
                    rows.push(`0x${slot.toString(16)}:${p} <- ` +
                        found.map(j => labels[j]).join('^'));
                }
            }
        });
        if (rows.length) console.log(`  op ${String(op).padStart(3)}: ${rows.join('  ')}`);
    }
    console.log(`  ${solved} of ${total} changing native bits have a port row; the rest name the gap`);
    void mine;
    process.exit(0);
}
if (process.argv.includes('--twosource')) {
    // The seed cancels in a delta, so the honest question about the arrangement is: which XOR of the
    // port's own per-case changes, each moved by a fixed shift, is the native case's change - in
    // every case. Two sources over the flag channels; a rule of this shape can be wrong, and the
    // count of cases it gets wrong is printed.
    const FLAT = ['flags', 'flags2', 'title flags'];
    const rows = [];
    for (const row of proof.cases) {
        if (row.fault) continue;
        const b = Buffer.from(row.before, 'hex');
        const a = Buffer.from(row.context, 'hex');
        c.reset(row.value | 0, row.variant);
        const before = NAMES.map(x => x.get());
        c.run(row.op, row.value | 0, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
        const after = NAMES.map(x => x.get());
        rows.push({b, a, d: after.map((v, i) => (v ^ before[i]) >>> 0)});
    }
    for (const slot of wanted) {
        const deltas = rows.map(r => (r.a.readUInt32LE(slot) ^ r.b.readUInt32LE(slot)) >>> 0);
        const live = deltas.filter(d => d).length;
        const idx = FLAT.map(n => NAMES.findIndex(x => x.name === n));
        const ranked = [];
        for (let i = 0; i < idx.length; i++) {
            for (let j = 0; j < idx.length; j++) {
                for (let sa = 0; sa < 32; sa++) {
                    for (let sb = 0; sb < 32; sb++) {
                        let hits = 0;
                        let bad = 0;
                        for (let k = 0; k < rows.length; k++) {
                            const cand = (((rows[k].d[idx[i]] << sa) >>> 0) ^
                                          ((rows[k].d[idx[j]] << sb) >>> 0)) >>> 0;
                            if (cand === deltas[k]) hits++;
                            else if (deltas[k]) bad++;
                        }
                        if (bad <= live * 0.02) {
                            ranked.push({i, j, sa, sb, hits, bad});
                        }
                    }
                }
            }
        }
        ranked.sort((x, y) => (x.bad - y.bad) || (y.hits - x.hits));
        console.log(`  native 0x${slot.toString(16)}: ${live} of ${rows.length} cases change it`);
        for (const r of ranked.slice(0, 3)) {
            console.log(`     ${FLAT[r.i]} << ${r.sa} xor ${FLAT[r.j]} << ${r.sb}: ` +
                `${r.bad} cases differ${r.bad === 0 ? '   EVERY CASE' : ''}`);
        }
        if (!ranked.length) console.log('     no two-source rule reaches two cases in a hundred wrong');
    }
    process.exit(0);
}
function popcount(x) { let n = 0; while (x) { x &= x - 1; n++; } return n; }
const rot = (x, s) => ((x << s) | (x >>> (32 - s))) >>> 0;
if (process.argv.includes('--bits')) {
    // A native word aggregates bits from several port fields, so no single channel and shift carries
    // the word. The finer question is where each native bit comes from: for every bit the native
    // values ever set, which named port bit carries it in every case.
    for (const s of wanted) {
        const values = native.get(s);
        const union = values.reduce((a, v) => a | v, 0) >>> 0;
        const live = [];
        for (let p = 0; p < 32; p++) {
            if (!((union >>> p) & 1)) continue;
            const vector = values.map(v => (v >>> p) & 1);
            if (vector.every(v => v === vector[0])) continue;   // a constant bit explains nothing
            live.push({p, vector});
        }
        console.log(`  native 0x${s.toString(16)}: ${live.length} bits that vary over ` +
            `${values.length} cases; union mask 0x${union.toString(16)}`);
        for (const {p, vector} of live) {
            let best = null;
            for (const x of NAMES) {
                const channel = channels.get(x.name);
                for (let q = 0; q < 32; q++) {
                    let hits = 0;
                    for (let i = 0; i < vector.length; i++) {
                        if ((((channel[i] >>> q) & 1)) === vector[i]) hits++;
                    }
                    if (!best || hits > best.hits) best = {channel: x.name, q, hits};
                }
            }
            console.log(`     native bit ${String(p).padStart(2)} -> ${best.channel} bit ` +
                `${String(best.q).padStart(2)}: ${best.hits} of ${vector.length}` +
                (best.hits === vector.length ? '   EVERY CASE' : ''));
        }
    }
    process.exit(0);
}
for (const s of wanted) {
    const values = native.get(s);
    const union = values.reduce((a, v) => a | v, 0) >>> 0;
    console.log(`  native ${s === undefined ? '' : '0x' + s.toString(16)}: ${values.length} cases, ` +
        `${new Set(values).size} distinct values, union mask 0x${union.toString(16)}`);
    const best = [];
    for (const x of NAMES) {
        const vector = channels.get(x.name);
        for (let shift = 0; shift < 32; shift++) {
            let hits = 0;
            for (let i = 0; i < values.length; i++) {
                if (((rot(vector[i], shift) & union) >>> 0) === values[i]) hits++;
            }
            if (hits > values.length * 0.9) best.push({channel: x.name, shift, hits});
        }
    }
    best.sort((a, b) => b.hits - a.hits);
    for (const row of best.slice(0, 4)) {
        console.log(`      ${row.channel} << ${row.shift}: ${row.hits} of ${values.length} cases` +
            (row.hits === values.length ? '   MATCHES EVERY CASE' : ''));
    }
    if (!best.length) console.log('      no channel and shift reaches nine cases in ten');
}
