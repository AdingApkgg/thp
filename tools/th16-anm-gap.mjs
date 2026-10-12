// Classify the two small gaps the checker found: which cases differ, and how the bits differ.
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
const root = process.argv[2];
mkdirSync(resolve(root, 'artifacts/th16/anm-check'), {recursive: true});
const bytes = readFileSync(resolve(root, 'artifacts/th16/anm-check/th16.wasm'));
const wasi = new WASI({version: 'preview1', args: [], env: {}, preopens: {}});
const {instance} = await WebAssembly.instantiate(bytes, {wasi_snapshot_preview1: wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const proof = JSON.parse(readFileSync(resolve(root, 'artifacts/th16/anm-native.json'), 'utf8'));
const WATCH = [
    {native: 0x18, name: 'flags', get: () => c.named(0) >>> 0},
    {native: 0x4ac, name: 'integer 0', get: () => c.named(6) >>> 0},
    {native: 0x4b0, name: 'integer 1', get: () => c.named(7) >>> 0},
    {native: 0x530, name: 'the flag word', get: () => c.named(2) >>> 0},
];
const buckets = new Map(WATCH.map(w => [w.name, new Map()]));
const examples = new Map(WATCH.map(w => [w.name, []]));
for (const row of proof.cases) {
    c.run(row.op, row.value | 0, row.variant, row.refs, row.arg | 0, row.arg2 | 0);
    const native = Buffer.from(row.context, 'hex');
    for (const w of WATCH) {
        const want = native.readUInt32LE(w.native);
        const got = w.get();
        if (want === got) continue;
        const key = `op=${row.op} variant=${row.variant} refs=${row.refs}`;
        buckets.get(w.name).set(key, (buckets.get(w.name).get(key) || 0) + 1);
        if (examples.get(w.name).length < 3) {
            examples.get(w.name).push(`op=${row.op} value=${row.value} variant=${row.variant} refs=${row.refs} native=0x${want.toString(16)} port=0x${got.toString(16)} xor=0x${(want ^ got).toString(16)}`);
        }
    }
}
const record = {game: 'th16', scope: 'Which cases of the first comparison differ, classified by opcode, value, variant and references. The slots are the ones the corpus touches; the verdict is from docs/porting/th16-anm-verified.json.',
  classes: {}, examples: {}};
for (const w of WATCH) {
    const map = buckets.get(w.name);
    const total = [...map.values()].reduce((a, b) => a + b, 0);
    console.log(`\n${w.name}: ${total} differing cases in ${map.size} classes`);
    record.classes[w.name] = {nativeSlot: `0x${w.native.toString(16)}`, total,
        byClass: Object.fromEntries([...map.entries()].sort())};
    record.examples[w.name] = examples.get(w.name);
    for (const [key, count] of [...map.entries()].sort()) console.log(`   ${key}: ${count}`);
    for (const line of examples.get(w.name)) console.log(`   e.g. ${line}`);
}
writeFileSync(resolve(root, 'docs/porting/th16-anm-gap.json'), JSON.stringify(record, null, 2) + '\n');
