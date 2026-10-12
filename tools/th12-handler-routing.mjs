#!/usr/bin/env node
// Find opcodes claimed by two different handlers, where the compiler cannot help.
//
// EnemyScript.cpp::command() calls enemy_movement_command() and
// enemy_emitter_command() *before* its routing chain. Each keeps its own
// `switch(op)` gate in a separate translation unit, so writing the same opcode
// into two of them is not a duplicate-case error - it is a silent shadow, and
// whichever runs first wins. That is how TH11's 0x1b4 sat in the emitter's gate
// and kept TH12's real 0x1b4 in EnemyStateCommands.cpp from ever running, which
// cost a wasm out-of-bounds trap and two rounds to trace.
//
// The routing chain is a chain of `else if`, so the first branch that matches
// wins and the rest never see the opcode.
//
// This reports every opcode where a pre-chain handler is matched AND the chain
// branch that would otherwise own it also has a case for it. It also reports
// opcodes a matched branch has no case for, because those refuse at runtime and
// are a different, quieter problem.
//
// Usage: node tools/th12-handler-routing.mjs [--check]

import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const GAME = path.join(ROOT, 'runtimes/th12/th12_web/cpp/game');
const read = (p) => fs.readFileSync(path.join(GAME, p), 'utf8');

const script = read('EnemyScript.cpp');

// The routing expressions, kept verbatim except for commands.manager, which is a
// runtime availability guard rather than an opcode condition, so it is read as
// present (a normal session has one).
//  If the file moves on without this tool,
// the tool must fail loudly rather than evaluate a stale copy of the rules.
const ROUTES = [
    {name: 'EnemyManager.cpp', text:
        'true&&((op>=0x100&&op<=0x10f&&op!=0x102&&op!=0x103&&op!=0x106&&op!=0x107&&op!=0x108&&op!=0x10d)||op==0x118||op==0x150||op==0x159||op==0x173||op==0x1c2||op==0x1a0)'},
    // Routed for exactly one opcode, so the branch owns a single case and no file
    // scan is needed.
    {name: 'enemy_fire_command', text: 'op==0x1f5', cases: new Set([0x1f5])},
    {name: 'EnemyLaserCommands.cpp', text:
        '(op>=0x19d&&op<=0x1a5&&op!=0x19e&&op!=0x1a5&&op!=0x1a0&&op!=0x1a1&&op!=0x1a2&&op!=0x1a3)||(op>=0x19c+0x10&&op<=0x1ad)||(op>=0x1af&&op<=0x1b2)||(op>=0x1be&&op<=0x1bf)'},
    {name: 'EnemyAnimations.cpp', text: 'op>=0x102&&op<=0x115'},
];
// The laser expression above is the source's, with `0x19c` written for the
// repeated left bound so it can be evaluated as one boolean. Verify the source
// still contains the pieces this depends on.
for (const needle of ['(op>=0x100&&op<=0x10f&&op!=0x102&&op!=0x103&&op!=0x106&&op!=0x107&&op!=0x108&&op!=0x10d)||op==0x118||op==0x150||op==0x159||op==0x173||op==0x1c2||op==0x1a0', '(op>=0x19d&&op<=0x1a5&&op!=0x19e&&op!=0x1a5&&op!=0x1a0&&op!=0x1a1&&op!=0x1a2&&op!=0x1a3)||(op>=0x1ac&&op<=0x1ad)||(op>=0x1af&&op<=0x1b2)||(op>=0x1be&&op<=0x1bf)']) {
    if (!script.includes(needle)) throw new Error(`routing expression not found in EnemyScript.cpp:\n${needle}`);
}
if (script.includes('0x1ac&&op<=0x1ad') === false) throw new Error('laser range changed');
if (!script.includes('op!=0x1a0&&op!=0x1a1&&op!=0x1a2&&op!=0x1a3)')) throw new Error('0x1a0, 0x1a1, 0x1a2 or 0x1a3 was routed back into the laser range');
// 0x1a1 is the screen shake, 0x1a2 is the dialogue starter and 0x1a3 is the dialogue wait; none spawns a
// laser, so all three must stay out of the laser range or their state bodies never run. Same failure 0x19c
// had, and for 0x1a2 it meant the engine never started a section dialogue at all.
if (!script.includes('op!=0x1a1&&op!=0x1a2&&op!=0x1a3)')) throw new Error('0x1a1, 0x1a2 or 0x1a3 was routed back into the laser range');
if (script.includes('op==0x16d||op==0x19a')) throw new Error('0x16d or 0x19a was routed back into the laser range');
// 0x16d is one of the 193 opcodes that resolve to the shared `xor eax,eax` epilogue, so the original does
// nothing with it and it must not acquire a laser body. 0x19a does have a body, but it is a state command
// (drops.primary = i(0) at 0x417a38), so routing it here would send it to the wrong dispatcher, which is the
// same failure 0x19c, 0x1a1, 0x1a2 and 0x1a3 had.
if (!script.includes('op>=0x19d&&op<=0x1a5')) throw new Error('laser range no longer starts at 0x19d');

const isCheck = process.argv.includes('--check');

// Case labels per handler file, in either spelling.
//
// EnemyManager.cpp writes its opcodes as `if(op==0x159)` rather than case labels,
// so a case-only scan left that branch's set empty and any shadow on it invisible.
// tools/th12-preechain-audit.mjs found 0x118 and 0x149 that way: both are claimed
// pre-chain and both would also be handled by the manager branch. They are safe
// today only because both are collision entries and get refused before either
// handler runs, which is luck rather than detection. So match both spellings, and
// report the refused ones below rather than silently skipping them - a detector
// that cannot be seen to fire is not evidence that nothing is there.
function caseSet(file) {
    const set = new Set();
    for (const m of read(file).matchAll(/case\s+(0x[0-9a-f]+|\d+)\s*:|op==(0x[0-9a-f]+|\d+)/g))
        set.add(Number(m[1] ?? m[2]));
    return set;
}

// The gate a handler advertises, i.e. the first `switch(op)` in its body.
function gateSet(file, signature) {
    const text = read(file);
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

const movement = gateSet('EnemyCommands.cpp', 'enemy_movement_command(');
const emitter = gateSet('EnemyEmitterCommands.cpp', 'enemy_emitter_command(');

const routes = ROUTES.map((r) => ({...r, test: new Function('op', `return !!(${r.text});`)}));
const cases = new Map(ROUTES.map((r) => [r.name, r.cases ?? caseSet(r.name)]));
const stateCases = caseSet('EnemyStateCommands.cpp');

// Opcodes the engine refuses on purpose, listed in EnemyScript.cpp itself.
const colliding = new Set();
for (const m of script.match(/kTh12CollidingOpcodes\[\]=\{([\s\S]*?)\};/)[1].matchAll(/\d+/g)) colliding.add(Number(m[0]));

const branchOf = (op) => routes.find((r) => r.test(op)) ?? {name: 'EnemyStateCommands.cpp'};
const casesOf = (b) => (b.name === 'EnemyStateCommands.cpp' ? stateCases : cases.get(b.name));

const shadows = [];
const refusedShadows = [];
let owned = 0;
for (let op = 0x100; op <= 0x2ff; op++) {
    const pre = movement.has(op) ? 'enemy_movement_command' : emitter.has(op) ? 'enemy_emitter_command' : null;
    if (!pre) continue;
    owned++;
    // If a routing branch also carries a case for this opcode, that handler is dead
    // for this number and the pre-chain one wins - the 0x1b4 failure.
    const branch = branchOf(op);
    if (!casesOf(branch).has(op)) continue;
    // Refused opcodes never reach either handler, so the shadow cannot bite. Report
    // them anyway: that is how this detector is shown to be able to fire at all.
    if (colliding.has(op)) refusedShadows.push({op, pre, branch: branch.name});
    else shadows.push({op, pre, branch: branch.name});
}

// TH12 routes a large block of the extended range straight to FUN_004154d0's epilogue at 0x41962b,
// whose body is `xor eax,eax` and the SEH unwind: those opcodes do nothing at all. The port inherited
// TH11 bodies for many of them, so both handlers now check the no-op predicate before their switch.
// The predicate is per title - runtime_noop_opcode consults the table generated from the running title's own
// executable - so the check below looks for that name and also requires the title constant to exist; a handler
// that went back to a single hardcoded title's table would satisfy neither.
// Case labels therefore prove nothing here - the question is whether the guard runs first - and that
// ordering is exactly what matters, because deleting a guard would silently re-arm every dead body
// behind it and the state would drift from the original while every return value still matched.
const noops = new Set((JSON.parse(fs.readFileSync(path.join(ROOT, 'docs/th12/ecl-case-bodies.json'), 'utf8')).noops ?? []).map(Number));
if (noops.size === 0) throw new Error('ecl-case-bodies.json carries no noop list to check against');
const portTitle = read('PortTitle.hpp');
if (!portTitle.includes('kPortTitle')) throw new Error('PortTitle.hpp carries no kPortTitle constant');

function guardRunsBeforeSwitch(file) {
    const text = read(file);
    const guard = text.indexOf('runtime_noop_opcode(');
    const open = text.indexOf('switch(op){');
    return guard >= 0 && open >= 0 && guard < open;
}

// Every file carrying case labels for a th12 no-op opcode inherited a TH11 body for one. The routing
// chain in EnemyScript.cpp guards first, so the game path is safe, but these handlers are also called
// directly - the test exports call them one by one - so a missing guard is reachable even when the game
// path looks fine. Deleting one silently re-arms every dead body behind it, and the symptom is a state
// divergence with matching return values, which no return-value check can see.
const HANDLERS = ['EnemyCommands.cpp', 'EnemyEmitterCommands.cpp', 'EnemyStateCommands.cpp', 'EnemyLaserCommands.cpp'];
let unguarded = 0, inertOwned = 0;
for (const file of HANDLERS) {
    const text = read(file);
    const labels = new Set([...text.matchAll(/\bcase\s+(0x[0-9a-f]+|\d+)\s*:/g)].map((m) => Number(m[1])));
    const inert = [...labels].filter((op) => noops.has(op));
    if (inert.length === 0) { console.log(`${file}: no th12 no-op case labels`); continue; }
    inertOwned += inert.length;
    const ok = guardRunsBeforeSwitch(file);
    if (!ok) unguarded++;
    console.log(`${file}: ${inert.length} th12 no-op case labels, guard before switch: ${ok}`);
}
const scriptGuard = script.includes('if(runtime_noop_opcode(context.instruction->opcode))return 0;');
console.log(`EnemyScript.cpp::command guards th12 no-ops: ${scriptGuard}`);
console.log(`dead TH11 bodies sitting behind a guard: ${inertOwned}`);

const hex = (n) => '0x' + n.toString(16);
console.log(`movement gate: ${movement.size} opcodes, emitter gate: ${emitter.size} opcodes`);
console.log(`opcodes owned by a pre-chain handler: ${owned}`);
console.log(`of those, shadowing a routing branch: ${shadows.length}`);
for (const s of shadows) {
    console.log(`  ${hex(s.op)}: ${s.pre} runs first, ${s.branch} also handles it and never runs`);
}
console.log(`of those, shadowed but refused by kTh12CollidingOpcodes: ${refusedShadows.length}`);
for (const s of refusedShadows) {
    console.log(`  ${hex(s.op)}: ${s.pre} runs first, ${s.branch} also handles it - refused before either, harmless`);
}

if (isCheck) {
    if (shadows.length) {
        console.error(`\nFAIL: ${shadows.length} opcode(s) are shadowed by a pre-chain handler`);
        process.exit(1);
    }
    if (unguarded) {
        console.error(`\nFAIL: ${unguarded} handler(s) own a th12 no-op opcode and do not run the th12_noop_opcode guard before their switch`);
        process.exit(1);
    }
    if (!scriptGuard) {
        console.error('\nFAIL: EnemyScript.cpp::command no longer guards th12 no-op opcodes');
        process.exit(1);
    }
    console.log('\nno pre-chain handler shadows a routing branch');
    console.log(`${inertOwned} dead TH11 bodies stay inert behind the th12_noop_opcode guards`);
}
