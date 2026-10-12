// Builds the audit worklist for the th11 pre-chain residue.
//
// Why: th12 has a single dispatch switch (FUN_004154d0) and no pre-dispatch at all, so the
// port's pre-chain gates - movement and emitter - are TH11 architecture. The opcodes they
// claim therefore run TH11-derived bodies. Where TH11 and TH12 agree that is right by luck;
// where they disagree it is silently wrong. This tool lists them ranked by how often th12.dat
// actually uses them, together with what TH12's dispatcher really gives the number, so the
// audit works heaviest-first instead of waiting for the stage probe to collide.
//
// The gate extraction is copied from th12-handler-routing.mjs on purpose: it is the same
// brace-matched "first switch(op) after the signature" read, so the two tools cannot drift.
//
// Usage: node tools/th12-preechain-audit.mjs
import fs from 'node:fs';

const GAME = 'runtimes/th12/th12_web/cpp/game';

function gateSet(file, signature) {
    const text = fs.readFileSync(`${GAME}/${file}`, 'utf8');
    const at = text.indexOf(signature);
    if (at < 0) throw new Error(`${file}: ${signature} not found`);
    const open = text.indexOf('switch(op){', at);
    if (open < 0) throw new Error(`${file}: no switch(op) in ${signature}`);
    let depth = 0, end = open;
    for (let i = text.indexOf('{', open); i < text.length; i++) {
        if (text[i] === '{') depth++;
        else if (text[i] === '}') { depth--; if (!depth) { end = i; break; } }
    }
    const set = new Set();
    for (const m of text.slice(open, end).matchAll(/case\s+(0x[0-9a-f]+|\d+)\s*:/g)) set.add(Number(m[1]));
    return set;
}

const gates = {
    movement: gateSet('EnemyCommands.cpp', 'enemy_movement_command('),
    emitter: gateSet('EnemyEmitterCommands.cpp', 'enemy_emitter_command('),
};
const claims = new Map();
for (const [gate, set] of Object.entries(gates)) {
    for (const op of set) {
        if (!claims.has(op)) claims.set(op, []);
        claims.get(op).push(gate);
    }
}

const extended = JSON.parse(fs.readFileSync('docs/th12/ecl-extended-opcodes.json', 'utf8'));
const byOp = new Map();
for (const e of extended.entries ?? []) byOp.set(Number(e.opcode ?? e.id), e);

const bodies = JSON.parse(fs.readFileSync('docs/th12/ecl-case-bodies.json', 'utf8'));
const opToVA = new Map();
for (const [va, body] of Object.entries(bodies.bodies ?? {})) {
    for (const op of body.opcodes ?? []) opToVA.set(Number(op), {va, shared: (body.opcodes ?? []).length});
}

// The chain handlers. The manager branch is written with `if(op==0x159)` rather than a case
// label, so both forms are scanned - a worklist may over-approximate, an audit may not miss.
const chainFiles = ['EnemyManager.cpp', 'EnemyLaserCommands.cpp', 'EnemyAnimations.cpp', 'EnemyStateCommands.cpp'];
const chainSrc = chainFiles.map(f => [f, fs.existsSync(`${GAME}/${f}`) ? fs.readFileSync(`${GAME}/${f}`, 'utf8') : '']);
const chainHandled = op => {
    const hex = op.toString(16);
    const hits = [];
    for (const [f, src] of chainSrc) if (new RegExp(`case\\s+0x0*${hex}\\s*:|op==0x0*${hex}\\b`).test(src)) hits.push(f);
    return hits;
};

const rows = [...claims.entries()].map(([op, gateNames]) => {
    const e = byOp.get(op) ?? {};
    const b = opToVA.get(op) ?? {};
    return {
        op, hex: `0x${op.toString(16)}`,
        uses: e.used ?? e.usedInTh12Dat ?? 0,
        gates: gateNames.join('+'),
        va: b.va ?? '?', shared: b.shared ?? 0,
        verdict: e.verdict ?? '?',
        chain: chainHandled(op),
    };
}).sort((a, b) => b.uses - a.uses || a.op - b.op);

const count = k => [...claims.values()].filter(g => g.includes(k)).length;
console.log(`pre-chain claims: ${rows.length} opcodes (movement ${count('movement')}, emitter ${count('emitter')})`);
console.log('');
console.log('uses  opcode     gate       th12 case  shared  verdict               chain handler');
for (const r of rows) {
    console.log(
        String(r.uses).padStart(4), ' ', r.hex.padEnd(9), ' ', r.gates.padEnd(9), ' ',
        r.va.padEnd(9), ' ', String(r.shared).padStart(5), '  ', r.verdict.padEnd(20), ' ',
        r.chain.length ? r.chain.join(',') : '-'
    );
}
console.log('');
const heavy = rows.filter(r => r.uses > 0);
console.log(`${heavy.length} of ${rows.length} are used by th12.dat, total weight ${heavy.reduce((s, r) => s + r.uses, 0)} uses.`);
console.log(`claimed pre-chain AND reachable by a chain handler (shadow candidates): ${rows.filter(r => r.chain.length).length}`);
