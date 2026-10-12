import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/item-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-item-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-item-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'item.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/item-native.json'),'utf8'));
for(const r of proof.rewards){assert.equal((r.positionBits?c.reward_bits:c.reward)(r.seed,r.count,r.load,Number(r.full),r.generation,...(r.positionBits??r.position)),0,JSON.stringify(r));assert.deepEqual(Array.from({length:29},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));}
for(const r of proof.ordinary){
 assert.equal(c.ordinary(r.kind,r.rate,...r.position,r.angle),0,JSON.stringify(r));
 assert.deepEqual(Array.from({length:29},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));
 const binds=r.events.filter(e=>e[0]===0);assert.deepEqual([c.script(),c.indicator_script()],binds.map(e=>e[1]));assert.equal(c.special_counter()>>>0,r.counter);assert.deepEqual(Array.from({length:c.notice_count()},(_,n)=>c.notice_value(n)>>>0),r.events.filter(e=>e[0]===4||e[0]===5).flat());
}
for(const r of proof.special){assert.equal(c.special_drop(r.counter,Number(r.full)),0,JSON.stringify(r));assert.deepEqual(Array.from({length:29},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));assert.equal(c.special_counter()>>>0,r.nextCounter);assert.deepEqual(Array.from({length:c.notice_count()},(_,n)=>c.notice_value(n)>>>0),r.events.filter(e=>e[0]===4||e[0]===5).flat());}
for(const r of proof.ticks){
 assert.equal(c.tick(r.state,r.rate,r.case,...r.position,...r.velocity),0,JSON.stringify(r));
 assert.deepEqual(Array.from({length:29},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));
 const binds=r.events.filter(e=>e[0]===0);if(binds.length)assert.equal(c.script(),binds[0][1]);
 assert.deepEqual(Array.from({length:c.sound_count()},(_,n)=>c.sound_value(n)>>>0),r.events.filter(e=>e[0]===2).flat(),JSON.stringify(r));
}
for(const r of proof.attraction){assert.equal(c.attraction_case(...r.input),0,JSON.stringify(r));assert.deepEqual(Array.from({length:29},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));assert.equal(c.combo_timer()>>>0,r.timer);assert.deepEqual(Array.from({length:c.notice_count()},(_,n)=>c.notice_value(n)>>>0),r.events.filter(e=>e[0]===4||e[0]===5).flat(),JSON.stringify(r));}
c.exhaust_begin();assert.deepEqual(proof.chains[1],Array.from({length:4096},(_,n)=>c.chain(n)));
for(const slot of proof.exhaustion.slots)assert.equal(c.exhaust_next(),slot);
assert.equal(c.value(18)>>>0,proof.exhaustion.count);assert.equal(c.value(21)>>>0,proof.exhaustion.rewardCount);assert.equal(c.value(22),proof.exhaustion.rngSeed);assert.equal(c.value(23),proof.exhaustion.rngCalls);
for(const r of proof.draws){
 assert.equal(c.draw(r.state,r.y,r.delay),0);assert.equal(c.draw_value(0),r.display,JSON.stringify(r));
 if(r.events.length)assert.deepEqual([1,2,3].map(n=>c.draw_value(n)>>>0),r.events[0].slice(2));
 assert.equal(c.draw_value(4),r.events.length,JSON.stringify(r));
}
assert.deepEqual([c.other_rng(0),c.other_rng(1)],[54321,123],'ANM/shake RNG remains untouched');
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/ItemManager.hpp','cpp/game/ItemManager.cpp','cpp/game/ItemTh14.cpp','cpp/game/ItemRewards.cpp','cpp/game/GameEconomy.cpp','cpp/game/BulletTh14.cpp','cpp/game/BulletManager.hpp','cpp/game/GameBattle.hpp','cpp/game/GameBattle.cpp','cpp/game/GameEconomy.hpp'];
const report={passed:true,ordinaryAllocationCases:proof.ordinary.length,specialDropCases:proof.special.length,rewardCases:proof.rewards.length,tickCases:proof.ticks.length,drawCases:proof.draws.length,exhaustionCalls:proof.exhaustion.slots.length,ordinaryCapacity:600,cancelCapacity:4096,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Both native and production item paths consume the 4db510 stream (animations.visual_rng) and preserve a seeded 4db508 ANM/shake stream. Retail 41d8c0 cancel free-list order, 41ae00 reward type 1 including strict f32 screen edges, actual 4034b0 RNG/439d80 polar math, wrapping counts and signed delay thresholds; 4,098 consecutive rewards exhaust the 4,096-slot pool and continue consuming RNG. Retail full 438550 tick covers cancel type 10 states 1/2/3/5, activation-frame skips, fall/homing, dead-player fallback, pickup counters and sound 37. Retail 439640 primary draw requests compare raw positions and the y=-8 indicator cutoff against synthetic command recording. Retail 4397b0 type 1..8 and special type 12 ordinary pool allocation, clamping, special-count wrapping/modulo-five conversion to 4/6, two ANM script requests and 439b50 effect-100/sound-74-or-48 delivery are compared. Includes full-pool special counter preservation. ANM cache/bind/tick/draw and zero-handle cleanup are controlled native boundaries; port scripts are synthetic. Ordinary attraction/combo behavior, ordinary types 3..8 collection, reward helper modes 2/3, complete Bomb/HUD/replay attraction gating, auxiliary effects, real bullet.anm activation pixels and GPU equivalence remain unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
report.ordinaryAttractionCases=proof.attraction.length;report.scope=report.scope.replace('Ordinary attraction/combo behavior, ordinary types 3..8 collection,', 'Retail full 438550 ordinary attraction compares 576 type 1/2/4/6 state 1/2/3/4 cases: character line edges, Bomb-first-60-tick and dialogue overrides, dead-player fallback, homing, delayed notice delivery, focused/unfocused proximity attraction at one-third speed, state-4 homing/promotion without combo refresh and eight-frame combo timer refresh/decrement. Combo collection/settlement is covered separately. Ordinary types 3/8 collection,');
writeFileSync(resolve(root,'docs/porting/th14-item-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.rewardCases} rewards, ${report.tickCases} cancel ticks, ${report.ordinaryAttractionCases} ordinary attraction cases, ${report.drawCases} draws, ${report.exhaustionCalls} depletion calls.`);
