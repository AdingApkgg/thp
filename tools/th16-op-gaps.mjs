// For every opcode the native corpus covers: does the port vocabulary hold a body that reproduces the
// original's XOR delta of the flag slots in EVERY one of the op's cases, through ONE fixed shift?
// The shift must map the union of the native deltas onto the union of the body deltas exactly, which
// is what stops a zero-annihilating shift from letting an idle body fit. Ops with no such body are
// the vocabulary gaps of this title, listed by measurement rather than by search.
import {readFileSync} from 'node:fs';
import {WASI} from 'node:wasi';
const SLOTS = [0x530, 0x534];
const corpus = JSON.parse(readFileSync('artifacts/th16/anm-native-all.json', 'utf8')).cases;
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(readFileSync('artifacts/th16/anm-check/th16.wasm'),
    {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const key = x => [x.value, x.variant, x.refs, x.arg, x.arg2].join('|');
const tuples = [];
const tupleIndex = new Map();
for (const x of corpus) {
    if (!tupleIndex.has(key(x))) { tupleIndex.set(key(x), tuples.length); tuples.push(x); }
}
const codes = [...Array(761).keys(), ...Array.from({length: 0x201}, (_, i) => 0x7000 + i)];
const cat = new Map();
for (const code of codes) {
    const per = [];
    let trapped = false;
    for (const t of tuples) {
        try {
            c.reset(Number(t.value) | 0, t.variant);
            const b0 = c.named(0) >>> 0, b1 = c.named(1) >>> 0;
            c.run(code, Number(t.value) | 0, t.variant, t.refs, Number(t.arg) | 0, Number(t.arg2) | 0);
            per.push([(((c.named(0) >>> 0) ^ b0)) >>> 0, (((c.named(1) >>> 0) ^ b1)) >>> 0]);
        } catch { trapped = true; break; }
    }
    if (!trapped) cat.set(code, per);
}
const delta = (x, off) => (Buffer.from(x.before, 'hex').readUInt32LE(off)
    ^ Buffer.from(x.context, 'hex').readUInt32LE(off)) >>> 0;

const byOp = new Map();
for (const x of corpus) { if (!byOp.has(x.op)) byOp.set(x.op, []); byOp.get(x.op).push(x); }
const covered = [];
const gaps = [];
for (const [op, rows] of [...byOp.entries()].sort((a, b) => a[0] - b[0])) {
    for (const off of SLOTS) {
        const want = rows.map(x => delta(x, off));
        const Mn = want.reduce((a, b) => a | b, 0) >>> 0;
        if (!Mn) continue;
        const idx = rows.map(x => tupleIndex.get(key(x)));
        const fits = [];
        for (const [code, per] of cat) {
            for (let word = 0; word < 2; word++) {
                const d = idx.map(i => per[i][word]);
                const Mp = d.reduce((a, b) => a | b, 0) >>> 0;
                if (!Mp) continue;
                for (let k = -31; k <= 31 && fits.length < 400; k++) {
                    const shifted = (k >= 0 ? (Mn << k) >>> 0 : (Mn >>> -k) >>> 0);
                    if (shifted !== Mp) continue;
                    if (!d.every((v, i) => v === (k >= 0 ? ((want[i] << k) >>> 0) : (want[i] >>> -k)))) continue;
                    fits.push(code + '(' + c.canonical(code) + ',' + (word ? 'flags2' : 'flags')
                        + ',k=' + k + ',0x' + Mp.toString(16) + ')');
                    break;
                }
            }
        }
        const distinct = [...new Set(want.filter(Boolean).map(v => '0x' + v.toString(16)))];
        const row = 'op ' + String(op).padEnd(5) + '0x' + off.toString(16) + ': '
            + rows.length + ' cases, ' + want.filter(Boolean).length + ' write, '
            + distinct.length + ' distinct deltas ' + distinct.join(' ');
        if (fits.length) covered.push(row + ' -> ' + fits.slice(0, 4).join(' '));
        else gaps.push(row + ' -> NO BODY');
    }
}
console.log('  ops with a write in a flag slot: ' + (covered.length + gaps.length)
    + '; with a fitting body: ' + covered.length + '; without: ' + gaps.length);
console.log('  --- the gaps, which are the vocabulary the port is missing ---');
for (const g of gaps) console.log('  ' + g);
console.log('  --- covered, first four bodies each ---');
for (const v of covered) console.log('  ' + v);
