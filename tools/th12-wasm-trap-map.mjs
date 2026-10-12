#!/usr/bin/env node
// Map V8 wasm trap frames back to C++ function names.
//
// Why the obvious approach fails: V8 reports `wasm-function[127]:0x16a18`, an index
// plus a module-level offset. llvm-objdump prints function start addresses, but a
// stripped module prints empty names (`<>:`) and a debug module names only the
// functions DWARF knows, so bracketing an offset against the *named* starts lands on
// whichever named function happens to precede it - which is what produced the
// nonsense mapping of every frame to timer_advance in round 21.
//
// What works: skip address bracketing entirely. llvm-objdump emits one header per
// function in code-section order, and the wasm's export section maps a name to a
// function index. Matching an exported name against its header position calibrates
// the index-to-position offset, and a majority vote across all exports makes that
// calibration robust. Then frame index minus offset indexes the header list directly.
//
// Needs a build made with TH12_CORE_DEBUG=1, because a stripped module has no names
// to recover.
//
// Usage:
//   llvm-objdump -d <wasm> > dis.txt
//   node tools/th12-wasm-trap-map.mjs <wasm> <dis.txt> [index:offset ...]
//
// With no frames given it reads crashFrames from artifacts/th12/stage-probe.json.

import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [wasmPath, disPath, ...frameArgs] = process.argv.slice(2);
if (!wasmPath || !disPath) {
    console.error('usage: node tools/th12-wasm-trap-map.mjs <wasm> <dis.txt> [index:offset ...]');
    process.exit(2);
}

function leb(bytes, at) {
    let result = 0, shift = 0, byte;
    do { byte = bytes[at.value++]; result |= (byte & 0x7f) << shift; shift += 7; } while (byte & 0x80);
    return result >>> 0;
}

// Export section, id 7: count, then (name, kind, index) triples. Only function
// exports matter here; they are the calibration anchors.
function functionExports(bytes) {
    const at = {value: 8};
    const exports = new Map();
    while (at.value < bytes.length) {
        const id = bytes[at.value++];
        const size = leb(bytes, at);
        const end = at.value + size;
        if (id === 7) {
            const count = leb(bytes, at);
            for (let i = 0; i < count; i++) {
                const length = leb(bytes, at);
                const name = bytes.toString('utf8', at.value, at.value + length);
                at.value += length;
                const kind = bytes[at.value++];
                const index = leb(bytes, at);
                if (kind === 0) exports.set(name, index);
            }
        }
        at.value = end;
    }
    return exports;
}

const bytes = fs.readFileSync(wasmPath);
const exports = functionExports(bytes);

// Every header line, in the order objdump emitted them. Empty names are kept:
// dropping them (as a naive `<(.+)>` match does) loses the position alignment.
const order = [];
const names = new Map();
for (const line of fs.readFileSync(disPath, 'utf8').split('\n')) {
    const m = line.match(/^[0-9a-f]+\s+<([^>]*)>:/);
    if (!m) continue;
    order.push(m[1]);
    if (m[1] && !names.has(m[1])) names.set(m[1], order.length - 1);
}

if (!order.length) {
    console.error('no function headers found in the disassembly');
    process.exit(1);
}

// Calibrate with the first occurrence of each unique export name. Inside the walk
// this must break after the first *header* (not after the first unique header), or a
// duplicated name scans on and skews its delta.
const firstPosition = new Map();
order.forEach((name, position) => {
    if (name && !firstPosition.has(name)) firstPosition.set(name, position);
});
const occurrences = new Map();
for (const name of order) if (name) occurrences.set(name, (occurrences.get(name) ?? 0) + 1);

const votes = new Map();
for (const [name, index] of exports) {
    if (occurrences.get(name) !== 1) continue;   // ambiguous anchor
    const position = firstPosition.get(name);
    if (position === undefined) continue;
    const delta = index - position;
    votes.set(delta, (votes.get(delta) ?? 0) + 1);
}
const best = [...votes.entries()].sort((a, b) => b[1] - a[1] || Math.abs(a[0]) - Math.abs(b[0]))[0];
if (!best) {
    console.error('could not calibrate: no exported name appears in the disassembly');
    process.exit(1);
}
const [offset, agreeing] = best;

console.log(`headers: ${order.length}, function exports: ${exports.size}`);
console.log(`calibrated index offset: ${offset} (${agreeing} export(s) agree, ${votes.size} candidate(s))`);
if (agreeing < 3) console.log('WARNING: weak calibration, treat the mapping below as unconfirmed');

let frames = frameArgs;
if (!frames.length) {
    const probe = path.join(ROOT, 'artifacts/th12/stage-probe.json');
    if (fs.existsSync(probe)) {
        const stages = JSON.parse(fs.readFileSync(probe, 'utf8')).stages;
        frames = stages.flatMap((s) => s.crashFrames ?? []);
    }
}
if (!frames.length) {
    console.log('no frames to map');
    process.exit(0);
}

console.log('--- frames ---');
for (const frame of frames) {
    const [indexText, offsetText] = frame.split(':');
    const index = Number(indexText);
    const position = index - offset;
    const name = order[position];
    console.log(`  wasm-function[${index}]${offsetText ? ' @' + offsetText : ''} -> ` +
        (name ? `${name}` : `(position ${position}, unnamed)`));
}
