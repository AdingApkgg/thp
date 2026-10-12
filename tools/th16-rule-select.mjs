// Which canonical body reproduces a measured command, judged only by measured quantities.
//
// The pipeline that found the title-16 row for 302 and the fifth-bit defect, written once: for an
// opcode, take the corpus's own record of the offsets it changes and the values it writes, then walk
// every canonical body of the title-16 build across the fixture's fifteen named quantities and ask which
// (body, member) pair puts the same value there in all forty measured cases while the pointer advances
// by the stored length. The old tables' own rows are printed beside the answer: when the measurement
// and the older titles agree, the title-16 row is a lookup with a measured witness instead of a guess.
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

// The commands worth a walk: the older tables already name bodies for them, and the corpus shows one
// context word written per case. The target column is what the older tables say the body is.
const CANDIDATES = [
    {op: 306, olderTablesName: 'anm_th13_flag15 (th13 and th14), while the title-16 block says 28675'},
    {op: 310, olderTablesName: '72 (th13 and th14)'},
    {op: 311, olderTablesName: 'anm_th14_rgb / 89 (th13)'},
    {op: 313, olderTablesName: 'anm_th14_resolution (th14)'},
    {op: 314, olderTablesName: 'anm_th14_flag22 (th14)'},
    {op: 305, olderTablesName: '73 (th13 and th14)'},
];

const corpus = JSON.parse(readFileSync(resolve(root, 'artifacts/th16/anm-native-all.json'), 'utf8'));
const wasm = resolve(out, 'rule-select.wasm');
execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
    '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--export-memory', '-DPORT_TITLE=16',
    ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
    {cwd: rt, stdio: 'pipe', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync(wasm), {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const MEMBERS = 15;

for (const {op, olderTablesName} of CANDIDATES) {
    const raw = corpus.cases.filter(r => r.op === op && !r.fault);
    const cases = raw.map(r => {
        const before = Buffer.from(r.before, 'hex'), after = Buffer.from(r.context, 'hex');
        const changed = [];
        for (let o = 0; o + 4 <= before.length; o += 4) {
            const b = before.readUInt32LE(o), a = after.readUInt32LE(o);
            if (b !== a && o !== 0x28) changed.push({offset: o, before: b, after: a});
        }
        return {r, changed, advance: (after.readUInt32LE(0x28) - before.readUInt32LE(0x28)) >>> 0};
    });
    const shaped = cases.filter(k => k.changed.length === 1);
    if (!shaped.length) { console.log(`op ${op}: no case writes exactly one context word`); continue; }
    const target = shaped[0].changed[0].offset;
    const oneWord = shaped.filter(k => k.changed[0].offset === target && k.advance === 12);
    // Only the cases where the original writes something are votes: a body that writes nothing must not
    // match a case whose measured value is unchanged, which is how the all-zero comparison degenerates.
    const interesting = oneWord.filter(k => (k.changed[0].after >>> 0) !== (k.changed[0].before >>> 0));
    const matches = [];
    if (interesting.length >= 2) for (let body = 0; body <= 760; body++) {
        for (let member = 0; member < MEMBERS; member++) {
            let hit = 0;
            for (const k of interesting) {
                c.reset(k.r.value | 0, k.r.variant);
                const was = c.named(member) >>> 0;
                const status = c.step(body, k.r.variant, k.r.refs, k.r.arg | 0, k.r.arg2 | 0);
                const now = c.named(member) >>> 0;
                const want = ((k.changed[0].after >>> 0) - (k.changed[0].before >>> 0)) >>> 0;
                if (status === 0 && (((now - was) >>> 0) === want) && (c.delta() >>> 0) === 12) hit++;
            }
            if (hit === interesting.length) matches.push({body, member, effective: c.canonical(body) >>> 0});
        }
    }
    const distinct = [...new Set(matches.map(m => `0x${(m.effective >>> 0).toString(16)}${m.body === m.effective ? '' : ` (through row from ${m.body})`}`))];
    console.log(`op ${op}: ${oneWord.length} of ${raw.length} cases write 0x${target.toString(16)} and advance by twelve,`
        + ` of them writing a nonzero value in ${interesting.length}`);
    console.log(`  older tables name: ${olderTablesName}`);
    console.log(`  command whose measured member moves by the same amount in every writing case:`
        + ` ${distinct.length <= 12 ? distinct.join(' ') : distinct.length + ' distinct commands'}`);
    const shown = [...new Map(matches.map(m => [m.effective, m])).values()].slice(0, 12)
        .map(m => `(0x${(m.effective >>> 0).toString(16)}, member ${m.member})`);
    if (shown.length) console.log(`  ${shown.join(' ')}`);
}
