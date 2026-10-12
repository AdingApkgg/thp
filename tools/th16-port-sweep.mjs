// The port side of the same grid the native signature sweep uses. For titles 12, 13 and 14 the
// interpreter reaches its whole canonical vocabulary, so this records what each of the port's canonical
// bodies does - the target vocabulary for the eventual th16 table - reduced the same way the native side
// was: the position delta, the named members that changed, and the raw offsets that changed. The
// fixture's `reset` and `step` are used separately so the state compared against is read, not
// remembered.
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const rt = resolve(root, 'runtimes/th12/th12_web');
const out = resolve(root, 'artifacts/th16/port-sweep');
const clang = resolve(root, 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const sources = ['AnmInterpreter', 'AnmVm', 'AnmGeometry', 'Interpolation', 'AnmResource'].map(s => `cpp/game/${s}.cpp`);
const fixture = 'tests/cpp/th16-anm-fixture.cpp';
// The native signature sweep's grid, case for case.
const GRID = [[0, 0, 0], [0, 0, 1], [18, 0, 0], [18, 0, 1], [1, 1, 0], [1, 1, 1], [2, 0, 1], [0, 1, 1]];
const REFERENCE_INDEX = 3;
const NAMED = ['flags', 'flags2', 'title flags', 'layer', 'color', 'secondary color',
               'integer 0', 'integer 1', 'live', 'timer', 'age', 'scale.x', 'scale.y', 'fraction'];
mkdirSync(out, {recursive: true});

async function load(title) {
    const wasm = resolve(out, `th${title}.wasm`);
    execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
        '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
        '-Wl,--no-entry', '-Wl,--export-memory', `-DPORT_TITLE=${title}`,
        ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
        {cwd: rt, stdio: 'pipe', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});
    const wasi = new WASI({version: 'preview1', args: [], env: {}, preopenss: 0, preopens: {}});
    const bytes = readFileSync(wasm);
    const {instance} = await WebAssembly.instantiate(bytes, {wasi_snapshot_preview1: wasi.wasiImport});
    wasi.initialize(instance);
    return {c: instance.exports, size: bytes.length};
}

const scratch = new Float32Array(1);
function realBits(c, which) {
    // Reading a float through >>> 0 truncates it first; what is compared is the bit pattern.
    scratch[0] = c.named_real(which);
    return new Uint32Array(scratch.buffer)[0];
}
function named(state, c) {
    const row = {};
    for (let i = 0; i < 11; i++) row[NAMED[i]] = c.named(i) >>> 0;
    row['scale.x'] = realBits(c, 0);
    row['scale.y'] = realBits(c, 1);
    row['fraction'] = realBits(c, 2);
    return row;
}
function slots(c) {
    const row = {};
    for (let o = 0; o + 4 <= (c.size() >>> 0); o += 4) row[`0x${o.toString(16)}`] = c.slot(o) >>> 0;
    return row;
}

const report = {scope: 'What each of the port\'s canonical bodies does under the native sweep\'s grid. ' +
    'Delta, changed named members and changed raw offsets. The target vocabulary for the th16 table.',
    grid: GRID, titles: {}};
for (const title of [12, 13, 14]) {
    const {c, size} = await load(title);
    const table = {};
    let mapped = 0, changed = 0, skipped = 0;
    for (let op = 0; op <= 0x2bc; op++) {
        const canonical = c.canonical(op) >>> 0;
        if (canonical === 0xffff) { skipped++; continue; }
        mapped++;
        const cases = [];
        let any = false;
        for (const [value, variant, refs] of GRID) {
            c.reset(value, variant);
            const beforeNamed = named(null, c), beforeSlots = slots(c);
            let status = 0, fault = false;
            try { status = c.step(op, variant, refs, refs ? REFERENCE_INDEX : value, value ^ 2); }
            catch (error) { fault = true; }
            const afterNamed = named(null, c), afterSlots = fault ? beforeSlots : slots(c);
            const namedAfter = afterNamed;
            const changedNamed = NAMED.filter(n => JSON.stringify(beforeNamed[n]) !== JSON.stringify(afterNamed[n]));
            const changedSlots = Object.keys(afterSlots).filter(o => beforeSlots[o] !== afterSlots[o]);
            if (changedNamed.length || changedSlots.length) any = true;
            cases.push({in: [value, variant, refs], status, fault, delta: c.delta() >>> 0,
                       canonical, changedNamed, changedSlots, namedAfter});
        }
        if (any) changed++;
        table[op] = {canonical, isDefault: canonical === 0, cases};
    }
    report.titles[title] = {wasmBytes: size, size: c.size() >>> 0, mapped, skipped, changed, table};
    console.log(`title ${title}: wasm ${size} bytes, sizeof ${c.size()}, ${mapped} opcodes map, ` +
                `${skipped} unmapped, ${changed} with an effect`);
}
writeFileSync(resolve(out, 'sweep.json'), JSON.stringify(report) + '\n');
console.log(`wrote artifacts/th16/port-sweep/sweep.json`);
