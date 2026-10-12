// Select the port body for this title's opcode 302 by the rule its handler shows, not by preference.
//
// The original at 0x4623dc, read off the machine: `mov eax,[edi+8]`, `shl eax,0x19`, XOR into the
// word at context 0x530 masked with 0x3e000000, write it back, and when the field reads 0x14000000
// call the helper at 0x469e20; then advance by the stored length. The corpus witness agrees to the
// bit - argument 1 toggles 0x02000000, argument 3 toggles 0x06000000 - and the position advances by
// twelve in all forty cases.
//
// So the quantity to compare is the toggle of the port's own flags word: the body that repeats this
// command toggles bits 25..29 of it by the resolved first argument and advances by twelve.
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
const OP = 302, SHIFT = 25, MASK = 0x3e000000;
const namedInTheFixture = 1;    // the fixture's own order: flags, flags2, then the rest
mkdirSync(out, {recursive: true});

const corpus = JSON.parse(readFileSync(resolve(root, 'artifacts/th16/anm-native-all.json'), 'utf8'));
const cases = corpus.cases.filter(c => c.op === OP && !c.fault).map(c => ({...c, index: c.refs ? c.arg : c.value}));
console.log(`opcode ${OP}: ${cases.length} measured cases`);
cases.slice(0, 4).forEach(c => {
    const before = Buffer.from(c.before, 'hex'), after = Buffer.from(c.context, 'hex');
    console.log(`  value ${String(c.value).padStart(6)} variant ${c.variant} refs ${c.refs} arg ${c.arg}`
        + ` -> context 0x530 ${(before.readUInt32LE(0x530)).toString(16)} to ${(after.readUInt32LE(0x530)).toString(16)}`
        + `, position +${after.readUInt32LE(0x28) - before.readUInt32LE(0x28)}`);
});

const wasm = resolve(out, 'rule-302.wasm');
execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
    '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--export-memory', '-DPORT_TITLE=16',
    ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
    {cwd: rt, stdio: 'pipe', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync(wasm), {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;

const wanted = (c2) => (((c2.index | 0) & 0x1f) << SHIFT) >>> 0;
const matches = [], near = [];
for (let body = 0; body <= 760; body++) {
    let toggled = 0, advanced = 0, finished = 0;
    for (const k of cases) {
        c.reset(k.value | 0, k.variant);
        const pre = c.named(namedInTheFixture) >>> 0;
        const status = c.step(body, k.variant, k.refs, k.arg | 0, k.arg2 | 0);
        const post = c.named(namedInTheFixture) >>> 0;
        if (((pre ^ post) >>> 0) === wanted(k)) toggled++;
        if ((c.delta() >>> 0) === 12) advanced++;
        if (status === 0) finished++;
    }
    const row = {body, toggled, advanced, finished};
    if (toggled === cases.length && advanced === cases.length) matches.push(row);
    else if (toggled + advanced > cases.length) near.push(row);
}
console.log(`${matches.length} of 761 bodies toggle the field by the resolved argument and advance by twelve`);
for (const row of matches.slice(0, 10)) console.log(`  ${JSON.stringify(row)}`);
if (!matches.length) {
    near.sort((a, b) => (b.toggled + b.advanced) - (a.toggled + a.advanced));
    for (const row of near.slice(0, 8)) console.log(`  near ${JSON.stringify(row)}`);
    const sample = cases.slice(0, 3).map(k => {
        c.reset(k.value | 0, k.variant);
        const pre = c.named(namedInTheFixture) >>> 0;
        c.step(0, k.variant, k.refs, k.arg | 0, k.arg2 | 0);
        return {index: k.index, want: `0x${wanted(k).toString(16)}`,
                observed: `0x${((pre ^ (c.named(namedInTheFixture) >>> 0)) >>> 0).toString(16)}`};
    });
    console.log(`  reference (body 0): ${JSON.stringify(sample)}`);
}

// The mapped body: the row sends this title's 302 to the command transcribed from 0x4623dc.
const mapped = c.canonical(OP) >>> 0;
{
    let toggled = 0, advanced = 0, finished = 0, deltas = new Set();
    for (const k of cases) {
        c.reset(k.value | 0, k.variant);
        const pre = c.named(namedInTheFixture) >>> 0;
        const status = c.step(mapped, k.variant, k.refs, k.arg | 0, k.arg2 | 0);
        const post = c.named(namedInTheFixture) >>> 0;
        if (((pre ^ post) >>> 0) === wanted(k)) toggled++;
        if ((c.delta() >>> 0) === 12) advanced++;
        if (status === 0) finished++;
    }
    console.log('the mapped body 0x' + mapped.toString(16) + ': toggled ' + toggled + '/40, advanced '
        + advanced + '/40, finished ' + finished + '/40 of the transcribed rule');

// The original's field holds the five-bit mode at bits 25..29 of its context word. This title's
// build lays the low four bits into flags 22..25 and the fifth bit elsewhere (set_drawing_mode,
// AnmVm.hpp:93, whose title branch names 13 and 14), so the same rule has to be read in this
// port's own bits before the row can be judged: flags toggles ((a & 15) << 22) | ((a & 16) << 25).
{
    let toggled = 0, advanced = 0, sample = null;
    const misses = [];
    for (const k of cases) {
        c.reset(k.value | 0, k.variant);
        const pre = c.named(0) >>> 0;
        const status = c.step(mapped, k.variant, k.refs, k.arg | 0, k.arg2 | 0);
        const post = c.named(0) >>> 0;
        const a = (k.index | 0) & 0x1f;
        const want = ((((a & 15) << 22) | ((a & 16) << 25)) >>> 0);
        if ((((pre ^ post) >>> 0) === want) && status === 0) toggled++;
        else misses.push({value: k.value, variant: k.variant, refs: k.refs, arg: k.arg,
                         observed: '0x' + ((pre ^ post) >>> 0).toString(16), want: '0x' + want.toString(16)});
        if ((c.delta() >>> 0) === 12) advanced++;
        if (sample === null) sample = {argument: a, observed: '0x' + ((pre ^ post) >>> 0).toString(16), want: '0x' + want.toString(16)};
    }
    console.log('the mapped body, in this port\'s own bits: ' + toggled + '/40 of the five-bit mode rule,'
        + ' advanced ' + advanced + '/40');
    for (const m of misses.slice(0, 6)) console.log('  differs: ' + JSON.stringify(m));
}
}
