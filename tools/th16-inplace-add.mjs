// Find the port body that repeats what this title's own opcode 102 does, measured on the instruction.
//
// The original at 0x460169 reads, off the machine: `test byte [edi+6],2`, the value resolver at
// 0x45f610 on argument 1, then `lea eax,[edi+8]`, the destination resolver at 0x45f890 on argument 0
// when its reference bit is set, then `add dword [eax],esi` - argument(0) plus argument(1), in the
// instruction - then `movzx eax,word [edi+2]`, `add [ebx+0x28],eax` and the tail jump.
//
// The declared layout agrees with the machine: AnmResource.hpp's AnmInstruction is
// `i16 opcode; u16 length; i16 time; u16 references;` with `argument(n)` at +8+4n, which is where
// the machine memory-maps references (+6) and the arguments (+8). This walks every canonical body of
// the title-12 build, where all of them are reached, over the same forty cases, and reports the ones
// that leave that whole command behind - plus a scan of the fixture's own code bytes, so a body's
// reading and writing are pinned to words rather than assumed.
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
const VALUES = [0, 1, 3, 18, 19, 255, 256, -1, 10000, 10001];
const REFERENCE_INDEX = 3;
const MARK0 = 0x11111111, MARK1 = 0x22222222;
mkdirSync(out, {recursive: true});

const wasm = resolve(out, 'inplace-add.wasm');
execFileSync(clang, ['--target=wasm32-wasip1', '-std=c++17', '-O2', '-ffp-contract=off',
    '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor',
    '-Wl,--no-entry', '-Wl,--export-memory', '-DPORT_TITLE=12',
    ...sources.map(s => resolve(rt, s)), resolve(rt, fixture), '-o', wasm],
    {cwd: rt, stdio: 'pipe', windowsHide: true, env: {...process.env, TEMP: out, TMP: out, TMPDIR: out}});
console.log(`built ${wasm}`);
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync(wasm), {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const hex = v => '0x' + (v >>> 0).toString(16).padStart(8, '0');

// The scan: where do the fixture's markers actually come back from? One run, distinctive arguments.
const status0 = c.run(0, 5, 0, 1, MARK0, MARK1);
const words = [];
for (let o = 0; o + 4 <= 32; o += 4) words.push(`+${o}:${hex(c.code_word(o))}`);
console.log(`scan of the fixture's code bytes, body 0, a run with marks ${hex(MARK0)} and ${hex(MARK1)}:`);
console.log(`  status ${status0} state +6:${hex(c.code_word(6))} integers0 ${hex(c.named(6))} delta ${c.delta() >>> 0}`);
console.log(`  ${words.join(' ')}`);
console.log(`  mark0 found at ${['+0', '+4', '+8', '+12', '+16', '+20', '+24', '+28'].filter((_, i) => (c.code_word(i * 4) >>> 0) === MARK0).join(',') || 'nowhere'}` +
            ` mark1 at ${['+0', '+4', '+8', '+12', '+16', '+20', '+24', '+28'].filter((_, i) => (c.code_word(i * 4) >>> 0) === MARK1).join(',') || 'nowhere'}`);

const cases = [];
for (const value of VALUES) for (const variant of [0, 1]) for (const refs of [0, 1]) {
    const arg = refs ? REFERENCE_INDEX : value;
    const arg2 = value ^ 2;
    cases.push({value, variant, refs, arg, arg2, wantFirst: (arg + arg2) >>> 0, wantSecond: arg2 >>> 0});
}
const matches = [];
const fingerprint = [];
for (let body = 0; body <= 760; body++) {
    let first = 0, second = 0, advanced = 0, finished = 0;
    for (const k of cases) {
        const status = c.run(body, k.value | 0, k.variant, k.refs, k.arg | 0, k.arg2 | 0);
        if (status === 0) finished++;
        if ((c.code_word(8) >>> 0) === k.wantFirst) first++;
        if ((c.code_word(12) >>> 0) === k.wantSecond) second++;
        if ((c.delta() >>> 0) === (body === 312 ? 16 : 12)) advanced++;
    }
    const row = {body, first, second, advanced, finished};
    if (first === cases.length && second === cases.length && advanced === cases.length) matches.push(row);
    if (body === 0 || (finished === cases.length && advanced === cases.length) || body === 102) fingerprint.push(row);
}
console.log('per-body counts (body 0, the fully finishing bodies, and 102):');
for (const row of fingerprint.slice(0, 40))
    console.log(`  body ${String(row.body).padStart(3)} first ${row.first}/40 second ${row.second}/40 advance ${row.advanced}/40 finished ${row.finished}/40`);
console.log(`${matches.length} of 761 bodies repeat the whole of it`);
for (const row of matches.slice(0, 12)) console.log(`  ${JSON.stringify(row)}`);
if (matches.length) {
    const chosen = matches[0].body, k = cases[9];
    const status = c.run(chosen, k.value | 0, k.variant, k.refs, k.arg | 0, k.arg2 | 0);
    console.log(`chosen body ${chosen}: status ${status}, first ${hex(c.code_word(8))}, second ${hex(c.code_word(12))}, delta ${c.delta() >>> 0}`);
}
