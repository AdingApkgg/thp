// Coverage matrix of the numbered flags: every single-bit writer of the title, the flag index the
// slot bit stands for, and the canonical bodies that already keep the home for that index.
// The two runs per body are the parity pair of section 322, so a write onto a preset bit is visible.
import {readFileSync} from 'node:fs';
import {WASI} from 'node:wasi';
const corpus = JSON.parse(readFileSync('artifacts/th16/anm-native-all.json', 'utf8')).cases;
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync('artifacts/th16/anm-check/th16.wasm'),
    {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;

// Which native op writes a single bit where. A mask with one bit set, seen in before^context.
const single = new Map();
for (const row of corpus) {
    if (row.fault) continue;
    for (const off of [0x530, 0x534]) {
        const m = (Buffer.from(row.before, 'hex').readUInt32LE(off)
            ^ Buffer.from(row.context, 'hex').readUInt32LE(off)) >>> 0;
        if (m && (m & (m - 1)) === 0) single.set(row.op + ':' + off, {op: row.op, off, mask: m});
    }
}
// Every canonical body the title can reach, with the parity pair of the two flag words.
const bodies = new Map();
let trapped = 0;
const codes = [];
for (let code = 0; code <= 760; code++) codes.push(code);
for (let code = 0x7000; code <= 0x7200; code++) codes.push(code);  // the named vocabulary
for (const code of codes) {
    const canon = c.canonical(code);
    const pair = [];
    try {
        for (const arg of [1, 0]) {
            c.reset(0, 0);
            const before = [c.named(0) >>> 0, c.named(1) >>> 0];
            c.run(code, 0, 0, 0, arg, 0);
            const after = [c.named(0) >>> 0, c.named(1) >>> 0];
            pair.push([(after[0] - before[0]) >>> 0, (after[1] - before[1]) >>> 0]);
        }
    } catch { trapped++; continue; }
    const mask = w => (pair[0][w] | ((0 - pair[1][w]) >>> 0)) >>> 0;
    const key = canon;
    if (!bodies.has(key)) bodies.set(key, {canon, flags: mask(0), flags2: mask(1), codes: []});
    bodies.get(key).codes.push(code);
}
const writersOf = (word, mask) => [...bodies.values()].filter(x => x[word] === mask)
    .map(x => x.canon + (x.codes.some(v => v < 256) ? '(' + x.codes.filter(v => v < 256)[0] + ')' : ''));

console.log('  single-bit native writers, and the home for the flag index each one stands for');
console.log('  op    slot    mask      index   bodies with that home');
for (const {op, off, mask} of [...single.values()].sort((x, y) => x.op - y.op)) {
    const bit = Math.log2(mask);
    const index = off === 0x534 ? bit - 1 : bit;
    const home = writersOf('flags2', 1 << index);
    console.log('  ' + String(op).padEnd(6) + ('0x' + off.toString(16)).padEnd(8)
        + ('0x' + mask.toString(16)).padEnd(10) + String(index).padEnd(8)
        + (home.join(' ') || 'NONE'));
}
console.log('  bodies per slot word, for reference: flags writers ' + writersOf('flags', 0).length
    + ', flags2 writers ' + [...bodies.values()].filter(x => x.flags2).length);
