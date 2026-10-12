import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/stage-completion-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-stage-completion-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-stage-completion-fixture.cpp',path=resolve(out,'stage-completion.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/stage-completion-native.json'),'utf8'));
for(const [i,row] of proof.rows.entries()){
 assert.equal(c.run(...['stage','difficulty','practice','replay','selection','continues','lives','bombs','score','count','clean'].map(k=>row[k])),1,`case${i}`);
 for(const [kind,key] of ['resultScore','bonus','countResult','cleanResult'].entries())assert.equal(c.value(kind,row.selection,row.difficulty)>>>0,row[key],`case${i} ${key}`);
 for(const [j,pair] of row.pairs.entries())for(let b=0;b<2;++b)assert.equal(c.pair(row.selection,j+1,b),pair[b],`case${i} pair${j+1}/${b}`);
 let exit=0;if(row.events.some(e=>e[0]==='replay_end'))exit=3;else if(row.events.some(e=>e[0]==='results'))exit=2;else if(row.transition===12)exit=1;
 assert.equal(c.value(4,0,0),exit,`case${i} exit`);
 assert.equal(c.value(6,0,0),1);assert.equal(c.value(7,0,0),1);assert.deepEqual(row.events.filter(e=>e[0]==='animation'),[['animation',112]]);
 assert.equal(c.value(8,0,0)>>>0,row.hudFlags,`case${i} native HUD result flags`);
 assert.equal(c.value(9,0,0),Number(row.ending),`case${i} independent ending-controller flag`);
 if(exit===1)assert.equal(c.value(5,0,0),row.nextStage);
 const p=c.serialized(row.selection),v=new DataView(c.memory.buffer);
 assert.equal(v.getUint32(p+0x7c0+row.difficulty*4,true),row.countResult);assert.equal(v.getUint32(p+0x7dc+row.difficulty*4,true),row.cleanResult);
 assert.equal(c.value(2,row.selection,row.difficulty)>>>0,row.countResult);assert.equal(c.value(3,row.selection,row.difficulty)>>>0,row.cleanResult);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const [i,row] of proof.clock.entries()){
 c.clock_run(row.frame,row.replay,row.force,row.active);
 assert.equal(c.clock_value(0)>>>0,row.resultFrame,`clock${i} frame`);
 assert.equal(c.clock_value(1),+!!row.fade,`clock${i} fade`);
 if(row.fade){assert.deepEqual(row.fade,[5,200,0,0,0]);assert.deepEqual(row.events.filter(e=>e[0]==='register').map(e=>e[2]),[16,73]);}
 const exit=row.events.some(e=>e[0]==='replay_end')?3:row.transition===15?4:row.transition===2?5:0;
 assert.equal(c.clock_value(2),exit,`clock${i} exit`);
}
for(const [n,r] of proof.resultClock.entries()){
 c.result_clock_run(r.flags,r.frame,r.speed);assert.deepEqual(Array.from({length:4},(_,k)=>c.result_clock_value(k)>>>0),r.words,`result clock ${n}`);
}
writeFileSync(resolve(root,'docs/porting/th14-stage-completion-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,endingClockCases:proof.clock.length,resultClockCases:proof.resultClock.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail436f90 and434c10 executed, with ANM allocation/binding/insertion, replay finalization/player callback and result/replay exit services controlled. Production StageCompletion compared for score/bonus, all48 practice pairs, capped clear and no-continue counters, next-stage/result/replay exit routes and actual ScoreFile serialization/reload. Includes every stage/difficulty, practice/replay, six equipment choices, signed overflow/unsigned score cap and counter boundaries. HUD result flag100 now compared explicitly. Retail42fdb0..42fe31 additionally checks160 result clock states with flags100/200/400 combinations, rates.25/.5/1/2 and signed frame boundaries: current/previous/fraction words and120-frame gate. Retail436620..436769 additionally proves80 unpaused ending-clock cases, integer wrap, frame180 fade request/type5/duration200/native draw registration73 and frame380 ending/title/replay requests; allocator/callback registration and replay exit are controlled. Does not prove GPU result animation or finalization services.',sourceHashes:Object.fromEntries([fixture,'cpp/game/StageCompletion.cpp','cpp/game/StageCompletion.hpp','cpp/game/ScoreFile.cpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-stage-completion-native.py','tools/th14-stage-completion-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} retail awards/flags/routes; ${proof.clock.length} ending clocks; ${proof.resultClock.length} independent result clocks`);
