#!/usr/bin/env node
// Detector: an if(op==0xNN){...} implementation body whose opcode no dispatch gate in the same
// file claims can never run.
//
// Why this exists: in round 37, 0x19b was removed from EnemyEmitterCommands.cpp's outer gate
// after TH12's dispatcher turned out to give that opcode the ring descriptor rather than an
// emitter body. The TH11 copy body, spelled `if(op==0x19b){...}`, was left behind and became
// unreachable. th12-dispatch-gate.mjs could not report it and should not be blamed for that: it
// compares gate labels against inner switch labels, and this body is neither. It is outside that
// gate's scope rather than a blind spot in what it does - and the claim that it was a blind spot
// was corrected in round 39's notes. This is the check the diagnosis actually needs.
//
// The check is deliberately conservative so it does not cry wolf:
//   * only files that have a gate-shaped switch(op) — a body of labels, breaks and
//     `default:return false;` — are examined, and a file with no such gate is skipped;
//   * an opcode is only flagged when no gate in that file claims it, because the gate returns
//     false before any later body can be reached;
//   * an if-body for an opcode the gate does claim is normal wiring and is not reported.
//
// Usage:
//   node tools/th12-orphan-bodies.mjs           report only
//   node tools/th12-orphan-bodies.mjs --check   exit 1 if any orphan body exists

import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIR = path.join(ROOT, 'runtimes', 'th12', 'th12_web', 'cpp', 'game');
const check = process.argv.includes('--check');
const hex = (v) => '0x' + v.toString(16);

// Brace-matched switch(op) bodies, as in the dispatch gate.
function switches(source) {
    const out = [];
    const re = /switch\s*\(\s*op\s*\)\s*\{/g;
    let m;
    while ((m = re.exec(source))) {
        const open = m.index + m[0].length - 1;
        let depth = 0, close = open;
        for (; close < source.length; close++) {
            if (source[close] === '{') depth++;
            else if (source[close] === '}' && --depth === 0) break;
        }
        out.push({start: m.index, body: source.slice(open, close + 1)});
        re.lastIndex = close;
    }
    return out;
}

const GATE = /default\s*:\s*return false\s*;/;
function gateLabels(body) {
    const found = new Set();
    for (const m of body.matchAll(/case\s+(0x[0-9a-fA-F]+)\s*:/g)) found.add(parseInt(m[1], 16));
    return found;
}
// A gate is a switch(op) whose only content is labels, breaks and the default refusal.
function gateBody(body) {
    if (!GATE.test(body)) return false;
    const residue = body
        .replace(/case\s+0x[0-9a-fA-F]+\s*:/g, '')
        .replace(/default\s*:\s*return false\s*;/g, '')
        .replace(/break\s*;/g, '')
        .replace(/[{}]/g, '')
        .trim();
    return residue === '';
}

const files = fs.readdirSync(DIR).filter((f) => /^Enemy.*\.cpp$/.test(f)).sort();
const findings = [];
let examined = 0, skipped = 0, bodies = 0;

for (const file of files) {
    const source = fs.readFileSync(path.join(DIR, file), 'utf8');
    const gates = switches(source).filter((s) => gateBody(s.body));
    if (!gates.length) { skipped++; continue; }
    examined++;
    const claimed = new Set();
    for (const gate of gates) for (const n of gateLabels(gate.body)) claimed.add(n);

    // Every if-body in the file, whatever its spacing: if(op==0x1a8), if (op == 0x1a8) and so on.
    const re = /if\s*\(\s*op\s*==\s*(0x[0-9a-fA-F]+)\s*\)\s*\{/g;
    let m;
    while ((m = re.exec(source))) {
        bodies++;
        const op = parseInt(m[1], 16);
        if (!claimed.has(op)) {
            const line = source.slice(0, m.index).split('\n').length;
            findings.push({file, op, line});
        }
    }
}

console.log(`command files with a gate: ${examined}, without: ${skipped}, if-bodies seen: ${bodies}`);
if (!findings.length) {
    console.log('every if(op==0x..) body sits behind a gate that claims its opcode');
} else {
    for (const f of findings) {
        console.log(`ORPHAN ${f.file}:${f.line}: if(op==${hex(f.op)}) is unreachable, no gate in this file claims ${hex(f.op)}`);
    }
    console.log(`\n${findings.length} orphan body/bodies. A body nothing releases does nothing, however correct it looks.`);
}
if (check && findings.length) process.exit(1);
if (!check) console.log('(report only; pass --check to make this a gate)');
