// Which canonical command reproduces a measured command - asked of every word of the port's own VM.
//
// The named-quantity version of this walk could only see eleven quantities, and two of them - the
// timer and the instruction pointer - move every frame, so a one-bit write matched hundreds of bodies.
// The fixture already exposes slot(byteOffset) and size(), so this version compares every aligned word
// of the port's VM against the measured word, per writing case, by delta. A (command, slot) pair is
// reported only when its deltas equal the measured deltas in every writing case and the pointer
// advances by the stored length; the older titles' rows are printed beside the answer.
import {readFileSync, mkdirSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const rt = resolve(root, 'runtimes/th12/th12_web');
const out = resolve(root, 'artifacts/th16/port-sweep');
const clang = resolve(root, 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const sources = ['AnmInterpreter', 'AnmVm', 'AnmGeometry', 'Interpolation', 'AnmResource']
    .map(s => `cpp/game/${s}.cpp`);
const fixture = 'tests/cpp/th16-anm-fixture.cpp';
mkdirSync(out, {recursive: true});

const WANT = [303, 304, 307, 308, 310, 313, 314, 300, 301];
const corpus = JSON.parse(readFileSync(resolve(root, 'artifacts/th16/anm-native-all.json'), 'utf8'));
const wasm = resolve(out, 'rule-select-slots.wasm');
execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
    '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--export-memory', '-DPORT_TITLE=16',
    ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
    {cwd: rt, stdio: 'pipe', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync(wasm), {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const nSlots = (c.size() >>> 0) >> 2;
const read = (vec) => { for (let i = 0; i < nSlots; i++) vec[i] = c.slot(i << 2) >>> 0; return vec; };

// Which slots are evidence, measured: a slot whose delta is identical for every body, in a case
// where the original writes, moves for reasons of the frame rather than of the command - the timer
// and the pointer's presence among them. The same pass pins the named quantities for the record.
const probe = corpus.cases.filter(r => !r.fault && r.op === WANT[0]);
const probeCase = probe[0];
const pre = new Uint32Array(nSlots), post = new Uint32Array(nSlots);
const firstDelta = new Int32Array(nSlots).fill(-2);
for (let body = 0; body <= 760; body++) {
    c.reset(probeCase.value | 0, probeCase.variant);
    read(pre);
    c.step(body, probeCase.variant, probeCase.refs, probeCase.arg | 0, probeCase.arg2 | 0);
    read(post);
    for (let s = 0; s < nSlots; s++) {
        const d = ((post[s] - pre[s]) >>> 0) | 0;
        if (firstDelta[s] === -2) firstDelta[s] = d;
        else if (firstDelta[s] !== d) firstDelta[s] = -1;
    }
}
const uninformative = new Set();
for (let s = 0; s < nSlots; s++) if (firstDelta[s] >= 0) uninformative.add(s);
c.reset(probeCase.value | 0, probeCase.variant);
read(pre);
const labels = [];
for (let k = 0; k <= 10; k++) {
    const value = c.named(k) >>> 0;
    const slots = [];
    for (let s = 0; s < nSlots; s++) if (pre[s] === value && value !== 0) slots.push('0x' + (s << 2).toString(16));
    if (slots.length) labels.push(`${k}:${slots.slice(0, 4).join('/')}`);
}
console.log(`port VM: ${nSlots} aligned words; ${uninformative.size} of them move identically for every`
    + ` body (frame quantities); named quantities at the probe state: ${labels.join(' ')}`);

for (const op of WANT) {
    const raw = corpus.cases.filter(r => r.op === op && !r.fault);
    const cases = raw.map(r => {
        const before = Buffer.from(r.before, 'hex'), after = Buffer.from(r.context, 'hex');
        const words = [];
        for (let o = 0; o + 4 <= before.length; o += 4) {
            const b = before.readUInt32LE(o), a = after.readUInt32LE(o);
            if (b !== a && o !== 0x28) words.push({offset: o, want: (a - b) >>> 0, post: a});
        }
        return {r, words, advance: (after.readUInt32LE(0x28) - before.readUInt32LE(0x28)) >>> 0};
    });
    const oneWord = cases.filter(k => k.words.length === 1 && k.advance === 12);
    const writing = oneWord.filter(k => k.words[0].want !== 0);
    if (writing.length < 2) { console.log(`op ${op}: ${oneWord.length} single-word cases, ${writing.length} writing`); continue; }
    const target = writing[0].words[0].offset;
    const votes = writing.filter(k => k.words[0].offset === target);
    const wanted = votes.map(k => k.words[0].want);
    // The other side of the measurement: cases where the original writes nothing at all. A slot that
    // moves there is moving for the frame's reasons, so it may not be the command's own word.
    const still = cases.filter(k => k.words.length === 0 && k.advance === 12);
    const distinctWants = new Set(wanted.map(w => `${w}`)).size;
    // A slot says something about a command only if the command can change it: eight sampled bodies
    // are run on every voting case, and a slot counts as body-sensitive when at least two of them
    // move it by different amounts. Frame quantities survive every other criterion and die here.
    const SAMPLE_BODIES = [0, 1, 7, 73, 74, 302, 760];
    const everSensitive = new Uint8Array(nSlots);
    for (const k of votes) {
        const seen = new Int32Array(nSlots).fill(-2);
        for (const b of SAMPLE_BODIES) {
            c.reset(k.r.value | 0, k.r.variant);
            read(pre);
            c.step(b, k.r.variant, k.r.refs, k.r.arg | 0, k.r.arg2 | 0);
            read(post);
            for (let s = 0; s < nSlots; s++) {
                const d = ((post[s] - pre[s]) >>> 0) | 0;
                if (seen[s] === -2) seen[s] = d;
                else if (seen[s] !== d) everSensitive[s] = 1;
            }
        }
    }
    const sensitiveCount = everSensitive.reduce((a, b) => a + b, 0);
    // What the sensitive words actually do, body by body, in the first writing case. A word that the
    // case moves for every body carries no body's contribution; one that moves for a body and not for
    // the others names that body.
    if (votes.length) {
        const k = votes[0];
        const columns = [];
        for (let b of SAMPLE_BODIES) {
            c.reset(k.r.value | 0, k.r.variant);
            read(pre);
            c.step(b, k.r.variant, k.r.refs, k.r.arg | 0, k.r.arg2 | 0);
            read(post);
            const cells = [];
            for (let s = 0; s < nSlots; s++) {
                if (!everSensitive[s]) continue;
                cells.push({slot: '0x' + (s << 2).toString(16), delta: (post[s] - pre[s]) >>> 0});
            }
            columns.push({body: b, cells});
        }
        for (const cell of columns[0].cells) {
            const line = columns.map(col => {
                const c2 = col.cells.find(x => x.slot === cell.slot);
                return `${col.body}:0x${c2.delta.toString(16)}`;
            }).join(' ');
            console.log(`    sensitive ${cell.slot} (measured 0x${wanted[0].toString(16)}) -> ${line}`);
        }
    }
    const results = [];
    const shiftOf = (d, want) => {
        // A shift that annihilates the measurement is not a relation (section 318): the shifted value
        // has to be nonzero, and so does the measurement.
        for (let k = 0; k <= 31; k++) {
            const s = (want << k) >>> 0;
            if (s !== 0 && s === d) return k;
        }
        for (let k = 1; k <= 31; k++) if ((want >>> k) !== 0 && (want >>> k) === d) return -k;
        return null;
    };
    let best = {hits: 0, body: -1, slot: -1, shift: 0};
    // The shift is calibrated on the first writing case and then has to hold for every other one. It is
    // calibrated per body, from that body's own reading, because the word the command writes is zero
    // until that body moves it (section 319): the calibration here is only the opening of a claim
    // that the whole measured pattern of deltas repeats under one shift.
    for (let body = 0; body <= 760; body++) {
        let alive = null;   // slots still matching; null means every slot is a candidate
        const shifts = new Int32Array(nSlots);
        for (let v = 0; v < votes.length; v++) {
            const k = votes[v];
            c.reset(k.r.value | 0, k.r.variant);
            read(pre);
            const status = c.step(body, k.r.variant, k.r.refs, k.r.arg | 0, k.r.arg2 | 0);
            if (status !== 0 || (c.delta() >>> 0) !== 12) { alive = new Set(); break; }
            read(post);
            const next = [];
            for (let s = 0; s < nSlots; s++) {
                if (uninformative.has(s)) continue;
                if (alive !== null && !alive.has(s)) continue;
                if (!everSensitive[s]) continue;
                const d = (post[s] - pre[s]) >>> 0;
                if (v === 0) {
                    const k2 = shiftOf(d, wanted[0]);
                    if (k2 === null) continue;
                    shifts[s] = k2;
                    next.push(s);
                    continue;
                }
                const g = shifts[s];
                if (d !== ((g >= 0 ? (wanted[v] << g) : (wanted[v] >>> -g)) >>> 0)) continue;
                next.push(s);
            }
            alive = new Set(next);
            if (!alive.size) break;
            if (v > best.hits) best = {hits: v, body, slot: [...alive][0] ?? -1, shift: shifts[[...alive][0] ?? 0]};
        }
        if (alive && alive.size && still.length) {
            for (const s0 of [...alive]) {
                for (const k of still) {
                    c.reset(k.r.value | 0, k.r.variant);
                    read(pre);
                    const status = c.step(body, k.r.variant, k.r.refs, k.r.arg | 0, k.r.arg2 | 0);
                    read(post);
                    if (status !== 0 || (c.delta() >>> 0) !== 12
                        || ((post[s0] - pre[s0]) >>> 0) !== 0) { alive.delete(s0); break; }
                }
            }
        }
        if (alive && alive.size) results.push({body, slots: [...alive].slice(0, 6), shift: shifts[[...alive][0]],
                                             effective: c.canonical(body) >>> 0});
    }
    const byCommand = new Map();
    for (const r of results) {
        const key = r.effective;
        if (!byCommand.has(key)) byCommand.set(key, new Set());
        for (const s of r.slots) byCommand.get(key).add(s << 2);
    }
    // Port slot offsets here are the ones this run measured, not the original's: flags 0x404, flags2
    // 0x408, layer 0x20, color 0x374, secondary color 0x378, integers[1] 0x3b8.
    const named = (off) => ({0x404: 'flags', 0x408: 'flags2', 0x20: 'layer', 0x374: 'color',
        0x378: 'secondary_color', 0x3b8: 'integers[1]', 0x5c: 'moves with the checker 0x544 slot'})[off] || '';
    const measured = [...new Set(wanted)].map(w => '0x' + w.toString(16));
    console.log(`op ${op}: ${votes.length} writing cases write 0x${target.toString(16)} (${distinctWants}`
        + ` distinct deltas: ${measured.join(' ')}), and ${still.length} cases write nothing;`
        + ` ${sensitiveCount} of the ${nSlots} words move differently for different bodies`);
    console.log(`  commands whose word at some slot moves by a fixed shift of the measured delta,`
        + ` in every vote: ${results.length} bodies`);
    for (const [cmd, slots] of [...byCommand].slice(0, 8)) {
        const shift = results.find(r => r.effective === cmd)?.shift ?? 0;
        const list = [...slots].slice(0, 6).map(s => '0x' + s.toString(16) + (named(s) ? ' (' + named(s) + ')' : '')).join(' ');
        console.log(`    0x${cmd.toString(16).padStart(4, '0')} shift ${shift >= 0 ? '+' : ''}${shift} -> ${list}`);
    }
}
