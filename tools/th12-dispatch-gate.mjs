#!/usr/bin/env node
// Gate: every case inside a command implementation switch must be released by the
// dispatch gate that precedes it in the same function.
//
// Why this exists: EnemyEmitterCommands.cpp reaches its inner switch through an
// outer `switch(op){case ...:break;default:return false;}` gate. In round 16 two
// cases (0x1fa and 0x1ff) were written into the inner switch but never added to
// that gate, so they were unreachable and did nothing - while the delivery notes
// claimed they had landed. The edits had been string replacements, and Replace
// does not fail when its target is missing, so nothing surfaced the drift.
//
// The check is deliberately structural rather than a fixed list: it finds every
// gate-shaped switch(op) (one whose body is only labels, breaks and
// `default:return false;`), pairs it with the next implementation switch(op), and
// diffs the two label sets. Labels handled by an `if(op==0x..)` block between the
// gate and the implementation count as released too, which is how the emitter's
// two-input copies (0x19b, 0x1ff) are wired.
//
// Usage:
//   node tools/th12-dispatch-gate.mjs           report only
//   node tools/th12-dispatch-gate.mjs --check   exit 1 if any label is unreachable

import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIR = path.join(ROOT, 'runtimes', 'th12', 'th12_web', 'cpp', 'game');
const check = process.argv.includes('--check');

const hex = (v) => '0x' + v.toString(16);

function labels(block) {
    const found = new Set();
    for (const m of block.matchAll(/case\s+(0x[0-9a-fA-F]+)\s*:/g)) found.add(parseInt(m[1], 16));
    return found;
}

// Find every `switch(op){...}` with brace matching, so nested switches and braces
// inside strings cannot throw the scan off.
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

const files = fs.readdirSync(DIR).filter((f) => /^Enemy.*\.cpp$/.test(f)).sort();
let paired = 0;
const findings = [];

for (const file of files) {
    const source = fs.readFileSync(path.join(DIR, file), 'utf8');
    const list = switches(source);
    for (let i = 0; i < list.length; i++) {
        // A gate is a switch(op) whose body is only case labels, breaks and the
        // default refusal. Anything with real statements is an implementation.
        if (!GATE.test(list[i].body)) continue;
        // Strip labels, `break;`, `default:return false;` and braces; if anything
        // is left it was an implementation switch, not a gate.
        const residue = list[i].body
            .replace(/case\s+0x[0-9a-fA-F]+\s*:/g, '')
            .replace(/default\s*:\s*return false\s*;/g, '')
            .replace(/break\s*;/g, '')
            .replace(/[{}]/g, '')
            .trim();
        if (residue) continue;

        const next = list[i + 1];
        if (!next || GATE.test(next.body)) continue;
        paired++;

        const gate = labels(list[i].body);
        const inner = labels(next.body);
        const special = new Set();
        for (const m of source.slice(list[i].start, next.start).matchAll(/if\s*\(\s*op\s*==\s*(0x[0-9a-fA-F]+)\s*\)/g)) {
            special.add(parseInt(m[1], 16));
        }

        const missing = [...inner].filter((v) => !gate.has(v) && !special.has(v)).sort((a, b) => a - b);
        const orphan = [...gate].filter((v) => !inner.has(v) && !special.has(v)).sort((a, b) => a - b);
        if (missing.length) findings.push({file, gate: gate.size, inner: inner.size, missing, orphan});
    }
}

// --- routing coverage -------------------------------------------------------
// EnemyScript.cpp::command() dispatches some opcodes to their own files through
// opcode conditions rather than through a per-file gate: the laser family and
// the animation family. A case in one of those files that its routing condition
// does not cover is exactly as dead as a case the inner gate never released -
// the same round-16 failure mode, one layer up. Parse the two conditions out of
// command() and evaluate them over the opcode range.

function splitTop(expr, separator) {
    const parts = [];
    let depth = 0, start = 0;
    for (let i = 0; i < expr.length; i++) {
        const ch = expr[i];
        if (ch === '(') depth++;
        else if (ch === ')') depth--;
        else if (depth === 0 && expr.startsWith(separator, i)) {
            parts.push(expr.slice(start, i));
            i += separator.length - 1;
            start = i + 1;
        }
    }
    parts.push(expr.slice(start));
    return parts;
}

const ATOM = /^(?:op|context\.instruction->opcode)\s*(==|!=|>=|<=)\s*(0x[0-9a-fA-F]+)$/;

function evalTerm(term, op) {
    let t = term.trim();
    while (t.startsWith('(') && t.endsWith(')')) t = t.slice(1, -1).trim();
    let sawOpcodeTest = false;
    for (const raw of splitTop(t, '&&')) {
        const m = raw.trim().match(ATOM);
        if (!m) continue;   // a guard such as commands.animations, not an opcode test
        sawOpcodeTest = true;
        const value = parseInt(m[2], 16);
        if (m[1] === '==' && op !== value) return false;
        if (m[1] === '!=' && op === value) return false;
        if (m[1] === '>=' && op < value) return false;
        if (m[1] === '<=' && op > value) return false;
    }
    // A term with no opcode test at all covers nothing; treating it as covering
    // everything would hide exactly the drift this check exists to find.
    return sawOpcodeTest;
}

function evalExpr(expr, op) {
    return splitTop(expr, '||').some((term) => evalTerm(term, op));
}

const scriptPath = path.join(DIR, 'EnemyScript.cpp');
const routed = [];
if (fs.existsSync(scriptPath)) {
    const script = fs.readFileSync(scriptPath, 'utf8');
    const patterns = [
        ['EnemyLaserCommands.cpp', /else if\((.+?)\)result=enemy_laser_command/],
        ['EnemyAnimations.cpp', /else if\((.+?)\)result=commands\.animations->command/],
    ];
    for (const [file, pattern] of patterns) {
        const m = script.match(pattern);
        if (!m) {
            findings.push({file, gate: 0, inner: 0, missing: [], orphan: [], note: 'routing condition not found in EnemyScript.cpp'});
            continue;
        }
        if (!fs.existsSync(path.join(DIR, file))) continue;
        const source = fs.readFileSync(path.join(DIR, file), 'utf8');
        const covered = new Set();
        const cases = new Set();
        for (const block of switches(source)) for (const v of labels(block.body)) cases.add(v);
        for (const op of cases) if (evalExpr(m[1], op)) covered.add(op);
        const unreached = [...cases].filter((op) => !covered.has(op)).sort((a, b) => a - b);
        routed.push({file, cases: cases.size, covered: covered.size});
        if (unreached.length) {
            findings.push({file, gate: covered.size, inner: cases.size, missing: unreached, orphan: [], routing: true});
        }
    }
}

console.log(`dispatch gates paired: ${paired} across ${files.length} command files`);
for (const r of routed) console.log(`routing coverage ${r.file}: ${r.covered}/${r.cases} cases reachable from command()`);
for (const f of findings) {
    if (f.note) {
        console.log(`UNREACHABLE ${f.file}: ${f.note}`);
        continue;
    }
    if (f.routing) console.log(`UNREACHABLE ${f.file}: ${f.missing.length} of ${f.inner} cases are not routed by command()`);
    else console.log(`UNREACHABLE ${f.file}: ${f.missing.length} of ${f.inner} inner cases are not released`);
    console.log(`  ${f.routing ? 'missing from routing' : 'missing from gate'}: ${f.missing.map(hex).join(' ')}`);
    if (f.orphan.length) console.log(`  gate labels with no inner case: ${f.orphan.map(hex).join(' ')}`);
}

if (findings.length) {
    console.log(`\n${findings.length} command file(s) have unreachable cases. A case that nothing releases or routes does nothing, no matter how correct it is.`);
    process.exit(1);
}
console.log('every inner case is released by its gate and routed by command()');
if (!check) console.log('(report only; pass --check to make this a gate)');

