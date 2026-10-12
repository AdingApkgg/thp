import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-state-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-enemy-state-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['EnemyTh14Commands','EnemyState','EclContext','Movement','Interpolation'].map(n=>'cpp/game/'+n+'.cpp');sources.push('tests/cpp/th14-enemy-state-fixture.cpp');
const wasm=resolve(out,'state.wasm');
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-enemy-state-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-state-native.json'),'utf8'));
for(const row of proof.cases){
 const p=c.allocate(29*4+16);new Uint32Array(c.memory.buffer,p,29).set(row.initial);new Uint32Array(c.memory.buffer,p+29*4,4).fill(0);new Uint32Array(c.memory.buffer,p+29*4,row.args.length).set(row.args);
 try{assert.equal(c.run(row.op,row.n,p,p+29*4),0,JSON.stringify(row));assert.deepEqual(Array.from({length:31},(_,i)=>c.value(i)>>>0),row.result,JSON.stringify(row));}finally{c.release(p);}
}
for(const row of proof.assignments){
 const p=c.allocate(20);new Uint32Array(c.memory.buffer,p,5).set(row.args);
 try{assert.equal(c.assign(row.op,row.difficulty,p)>>>0,row.result,JSON.stringify(row));}finally{c.release(p);}
}
for(const row of proof.bosses){
 assert.equal(c.boss_case(row.flags,row.managerFlags,row.selected,row.prior),0,JSON.stringify(row));
 assert.deepEqual(Array.from({length:19},(_,n)=>c.boss_value(n)>>>0),row.result,JSON.stringify(row));assert.equal(c.boss_global(),1);
}
assert.equal(c.boss_case(0,0,16,0),-2,'slot 16 overlaps native manager flags and remains unsupported');
for(const r of proof.bossWaits)assert.equal(c.boss_wait(r.pattern),r.result,`boss wait ${r.pattern}`);
for(const r of proof.dialogueWaits)assert.equal(c.dialogue_wait(r.present,r.signal),r.result,JSON.stringify(r));
for(const r of proof.phaseCounts)assert.equal(c.phase_count(r.value)>>>0,r.result,JSON.stringify(r));
for(const r of proof.clearCallbacks){assert.equal(c.clear_tick_callback(r.prior,r.mode,0),0);assert.deepEqual([c.tick_callback_word(0)>>>0,c.tick_callback_word(1)>>>0],r.result,JSON.stringify(r));}
assert.equal(c.clear_tick_callback(0,0,1),0,'nearest-bullet callback is supported');
assert.deepEqual([c.tick_callback_word(0)>>>0,c.tick_callback_word(1)>>>0],[1,0]);
assert.equal(c.clear_tick_callback(0,0,2),0,'screen-copy interrupt callback is supported');
assert.deepEqual([c.tick_callback_word(0)>>>0,c.tick_callback_word(1)>>>0],[2,0]);
assert.equal(c.clear_tick_callback(0,0,7),-2,'other TH14 callbacks remain unsupported');
for(const r of proof.callbackSetters){assert.equal(c.clear_tick_callback(r.prior,r.mode,r.index),0);assert.deepEqual([c.tick_callback_word(0)>>>0,c.tick_callback_word(1)>>>0],r.result,JSON.stringify(r));}
for(const r of proof.rates)for(const refs of [0,1])for(const connected of [0,1]){assert.equal(c.rate_case(r.value,refs,connected),0);assert.equal(c.rate_word(0)>>>0,r.result);assert.equal(c.rate_word(1)>>>0,connected?r.result:0x12345678);}
for(const row of proof.timers){assert.equal(c.timer_case(row.flags,row.pointer),0);assert.deepEqual(Array.from({length:5},(_,n)=>c.timer_value(n)>>>0),row.result,JSON.stringify(row));}
for(const r of proof.interrupts){assert.deepEqual(r.reads,[2,1,0]);assert.equal(c.interrupt_case(r.slot,r.health,r.time),0);assert.deepEqual(Array.from({length:4},(_,n)=>c.interrupt_value(r.slot,n)>>>0),r.result,JSON.stringify(r));}
for(const r of proof.timeoutNames){assert.deepEqual(r.reads,[0]);assert.equal(c.timeout_name_case(r.slot),0);assert.deepEqual(Array.from({length:4},(_,n)=>c.timeout_name_value(r.slot,n)>>>0),r.result,JSON.stringify(r));}
for(const r of proof.marks){assert.deepEqual(r.reads,[2,1,0]);assert.equal(c.mark_case(r.boss,r.slot,r.health,r.value,r.type),0);const actual=[c.mark_value(r.boss,r.slot,0)>>>0,c.mark_value(r.boss,r.slot,1)>>>0];
 // Division by zero yields platform NaN payloads; assert NaN classification.
 if(r.health===0&&r.value===0){assert.equal(actual[0]&0x7f800000,0x7f800000);assert.ok(actual[0]&0x7fffff);assert.equal(actual[1],r.result[1]);}else assert.deepEqual(actual,r.result,JSON.stringify(r));}
for(const r of proof.deathSounds)assert.equal(c.death_sound_case(r.value)>>>0,r.result,'553 '+r.value);
for(const r of proof.rewinds){const p=c.allocate(16);new Uint32Array(c.memory.buffer,p,4).set(r.counts);
 try{for(const refs of [0,15])assert.equal(c.rewind_case(r.difficulty,r.time,p,refs)>>>0,r.result,JSON.stringify({...r,refs}));}finally{c.release(p);}}
for(const r of proof.healthBits)for(const refs of [0,1])assert.equal(c.health_flag_case(r.flags,r.value,refs)>>>0,r.result,JSON.stringify(r));
for(const r of proof.hitboxAngles)for(const refs of [0,1])assert.equal(c.hitbox_angle_case(r.value,refs)>>>0,r.result,JSON.stringify(r));
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.cases.length,hitSoundSetterCases:proof.deathSounds.length,nativeExecutableSha256:proof.executableSha256,
 bossAssignments:proof.bosses.length,threadRewinds:proof.rewinds.length*2,hitboxAngleCases:proof.hitboxAngles.length*2,healthBitCases:proof.healthBits.length*2,globalSpeedCases:proof.rates.length*4,tickCallbackSetters:proof.callbackSetters.length,
 bossWaits:proof.bossWaits.length,
 dialogueWaits:proof.dialogueWaits.length,
 phaseCounts:proof.phaseCounts.length,
 clearedTickCallbacks:proof.clearCallbacks.length,
 timerResets:proof.timers.length,
 phaseInterrupts:proof.interrupts.length,healthMarks:proof.marks.length,
 timeoutNames:proof.timeoutNames.length,
 difficultyAssignments:proof.assignments.length,
 scope:'TH14 544 flag-bit-27 replacement, 553 hit-sound override, 500/501 boxes, 504/505 clamp fields, 506/507/508/510 thirteen-count drop descriptor, 511 health words, 512 boss registration/removal and manager flag, 513 timer reset, 514 ordinary-run interrupt setup, 519 dialogue release wait, 520 three-slot boss wait, 521 timeout name, 527 three-boss/four-mark health ratios, 524 section transition, 535/536 difficulty assignment, 540 remaining-phase count, 548 difficulty-selected thread-time rewinds with immediate/local arguments and 632 zero-index tick callback clearing. Native argument reads, destination lookup and memset are controlled boundaries; WASM assignment uses a real local reference. Spell-practice 514 setup, callback bodies (covered separately), full damage, clamp execution, drop spawning and replay behavior are not asserted.',
 wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EnemyState.hpp','cpp/game/EnemyCommands.hpp','cpp/game/GameBattle.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
report.scope+=' ECL 564 stores raw hitbox angle bits without normalization, in 22 immediate/local cases. The rotated shot-damage consumer is not implemented or asserted. ECL 568 replaces health flag bit 0, with 126 immediate/local cases compared against retail 4289cb. Retail 42978d ECL 547 writes global rate bits without clamping; 52 immediate/local and connected/standalone cases cover signed zero, subnormal, infinity and NaN payloads. The live target points at the ANM rate and is changed immediately at enemy priority. Native 4275e5 tick callback setters compare all supported indices 0..6 for 42 prior-pointer/mode cases.';
writeFileSync(resolve(root,'docs/porting/th14-enemy-state-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} TH14 field-setter cases; ${proof.assignments.length} difficulty assignments.`);
