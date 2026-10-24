import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-cancel-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-bullet-cancel-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-bullet-cancel-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'cancel.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-cancel-native.json'),'utf8'));
let rewardCases=0,rewardRequests=0;
for(const r of proof.cases){
 const label=JSON.stringify(r),needsReward=r.events.some(e=>e[0]===2&&e[1]!==0),result=(r.reward?c.run_reward:c.run)(r.state,r.flags,r.rate,...r.position);
 if(needsReward)++rewardRequests;
 if(r.reward)++rewardCases;
 assert.equal(result,0,label);assert.deepEqual(Array.from({length:9},(_,n)=>c.value(n)>>>0),r.result,label);assert.deepEqual(Array.from({length:c.event_size()},(_,n)=>c.event_value(n)>>>0),r.events.flat(),label);
}
for(const r of proof.delayedCases){assert.equal(c.run_delayed(r.state,r.flags,r.rate,...r.positionBits,r.delay),0,JSON.stringify(r));assert.deepEqual(Array.from({length:9},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));assert.deepEqual(Array.from({length:c.event_size()},(_,n)=>c.event_value(n)>>>0),r.events.flat(),JSON.stringify(r));}
for(const r of proof.allCases){assert.equal(c.run_all(r.state,r.flags,r.rate,...r.position,r.slot),0,JSON.stringify(r));assert.deepEqual(Array.from({length:9},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));assert.deepEqual(Array.from({length:c.event_size()},(_,n)=>c.event_value(n)>>>0),r.events.flat(),JSON.stringify(r));}
let changedRateCases=0;
for(const cachedRate of [.5,1,1.25])for(const r of proof.allCases){
 const label=JSON.stringify({cachedRate,...r});
 assert.equal(c.run_all_changed_rate(r.state,r.flags,cachedRate,r.rate,...r.position,r.slot),0,label);
 assert.deepEqual(Array.from({length:9},(_,n)=>c.value(n)>>>0),r.result,label);
 assert.deepEqual(Array.from({length:c.event_size()},(_,n)=>c.event_value(n)>>>0),r.events.flat(),label);++changedRateCases;
}
for(const op of [613])for(const r of proof.allCases){assert.equal(c.run_all_ecl(r.state,r.flags,r.rate,...r.position,r.slot,op),0,JSON.stringify({op,r}));assert.deepEqual(Array.from({length:9},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify({op,r}));assert.deepEqual(Array.from({length:c.event_size()},(_,n)=>c.event_value(n)>>>0),r.events.flat(),JSON.stringify({op,r}));}
for(const r of proof.timerCases){assert.equal(c.run_timer(r.value,r.flags,r.pointer),0);assert.deepEqual(Array.from({length:5},(_,n)=>c.timer_value(n)>>>0),r.result,JSON.stringify(r));}
for(const r of proof.etexCases){assert.equal(c.run_etex(r.state,r.flags,r.parameter,r.index,r.active,r.concurrent,r.rate),0,JSON.stringify(r));assert.deepEqual(Array.from({length:12},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));assert.deepEqual(Array.from({length:c.event_size()},(_,n)=>c.event_value(n)>>>0),r.events.flat(),JSON.stringify(r));}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletManager.cpp','cpp/game/BulletManager.hpp','cpp/game/PlayerFrame.cpp','cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp','cpp/game/GameBattle.cpp'];
const report={passed:true,cases:proof.cases.filter(r=>!r.reward).length,rewardCases,rewardRequests,delayedCircleCases:proof.delayedCases.length,allPoolCases:proof.allCases.length,changedRateCases,eclAllPoolCases:proof.allCases.length,timerSetCases:proof.timerCases.length,etexCancelCases:proof.etexCases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Also compares 360 cancellation cases after the current animation rate changes independently of the cached manager rate, covering all first/last pool-slot state and flag cases. Also compares 2304 actual 418140 ETEX 400 dispatch/cancellation cases: p equals 1 suppresses the effect, nonconcurrent active gating excludes bit 100, index advancement and all 41ac70 state/event writes are checked through the production environment and manager. Also compares actual 41b3f0 respawn circle: strict state 1/2, mandatory collision-delay filtering and ordered COMISS radius inclusion, including signed zero, NaN and infinity. Production GameBattle::cancel_bullets selects this TH14 path rather than legacy circle/erase-enemy/spell protection. The actual battle wrapper is source-wired; this fixture tests the manager boundary, not full Application execution. Retail 41b2f0 circle eligibility and 41ac70 primary-VM cancellation: strict state 1/2 gate, inclusive radius edge, flags 0x200 suppression, interrupt/effect/sound/reward request order, half-rate displacement, state 4 and lifetime reset. All 360 reward-circle cases now execute, including 48 controlled item delivery requests. Actual retail 41ae00 reward type 1 allocation, RNG, bounds, delay, pool exhaustion and subsequent item numerics are measured separately by th14-item-verified.json. Retail 41b880 full 2,000-slot pool scan covers the first/last slots, state-4 recancellation and the no-op reward helper with argument zero. Actual ECL 613 dispatch is checked through the production services/manager route with empty lasers, and 60 ECL 515 timer setters execute actual 4278e5/408b00. Retail 515 sets damage immunity; it is not a cancellation alias. Delivery factories are controlled boundaries here. Secondary appearance VMs, lasers and GPU pixels remain unverified; ECL 615/616 still refuse nonempty laser lists.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};writeFileSync(resolve(root,'docs/porting/th14-bullet-cancel-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.changedRateCases} live-rate changes; ${report.delayedCircleCases} respawn circles, ${report.cases} non-reward circle, ${report.rewardCases} reward-circle cases (${report.rewardRequests} delivery requests) and ${report.allPoolCases} full-pool cases; ${report.etexCancelCases} ETEX 400 cases.`);
