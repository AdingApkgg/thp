import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/time-drop-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-time-drop-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'time-drop.wasm'),fixture='tests/cpp/th16-time-drop-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/time-drop-native.json'),'utf8'));
for(const r of proof.setters){assert.equal(c.setter(r.flags,...r.args),0);assert.deepEqual(Array.from({length:7},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.ticks){c.tick(r.rate,r.current,r.fraction);assert.deepEqual(Array.from({length:3},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.decays){assert.equal(c.decay(r.duration,r.current,r.amount,r.minimum),1);assert.equal(c.value(5)>>>0,r.output,JSON.stringify(r));}
for(const r of proof.damageSetters){assert.equal(c.damage_setter(r.total,r.step),0);assert.deepEqual(Array.from({length:3},(_,n)=>c.damage_word(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.damageCases){c.damage_case(r.flags,r.amount,r.total);assert.deepEqual(Array.from({length:3},(_,n)=>c.health_word(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.healthSetters){assert.equal(c.health_setter(r.flags,r.health),0);assert.deepEqual(Array.from({length:5},(_,n)=>c.health_set_word(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.immunitySetters){assert.equal(c.immunity_setter(r.flags,r.duration),0);assert.deepEqual(Array.from({length:4},(_,n)=>c.immunity_word(n)>>>0),r.output,JSON.stringify(r));}
assert.equal(c.decay(0,1,10,1),0);assert.equal(c.decay(-1,1,-2147483648,0),0);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-time-drop-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,setters:proof.setters.length,countdowns:proof.ticks.length,scalarDeathCounts:proof.decays.length,nativeExecutableSha256:proof.executableSha256,scope:'Full retail1000 handler with controlled argument resolver; full40d490 countdown behind observed41d4f3 guard; scalar41d5ee..41d620 death-count fragment, signed multiplication and division. Production setter routes through EnemyScriptServices. Actual item allocation, scatter, damage drops and complete enemy frame/death are not covered.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/EnemyTh16Commands.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyState.cpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyCommands.hpp','cpp/game/Timer.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
const reportPath=resolve(root,'docs/porting/th16-time-drop-verified.json'),report=JSON.parse(readFileSync(reportPath,'utf8'));
report.damageDropSetters=proof.damageSetters.length;report.healthConsumers=proof.damageCases.length;report.immunitySetters=proof.immunitySetters.length;report.scope+=' Full own1001 snapshots received-damage counter; full41a6d0 health/sevenths/cumulative-damage consumer includes signed wrapping. Own515/4206bf executes retail406490 Timer setter, comparing all scalar timer fields and flags across signed boundaries; argument resolver controlled, pointer representation excluded. Seasonal item factory430960 and actual damage-drop emission remain explicit gaps.';report.sourceHashes['cpp/game/EnemyPhase.cpp']=sha(readFileSync(resolve(rt,'cpp/game/EnemyPhase.cpp')));writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(`PASS ${proof.setters.length} TH16 setters, ${proof.ticks.length} countdowns, ${proof.decays.length} scalar death counts, ${proof.damageSetters.length} damage-drop setters, ${proof.damageCases.length} health consumers`);
