import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-sakuya-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-shot-sakuya-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-shot-sakuya-fixture.cpp','cpp/game/ShotSakuyaTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'sakuya.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-sakuya-native.json'),'utf8'));
for(const r of proof.spawns){assert.equal(c.spawn(...r.args),Number(r.accepted),JSON.stringify(r.args));assert.deepEqual(Array.from({length:12},(_,i)=>c.value(i)>>>0),r.result,JSON.stringify(r.args));}
for(const r of proof.updates){new Uint32Array(c.memory.buffer,c.input(),22).set(r.args);assert.equal(c.update(),1,JSON.stringify(r.args));const actual=Array.from({length:27},(_,i)=>c.update_value(i)>>>0),actions=Array.from({length:7},(_,i)=>c.action_value(i)>>>0);
 if(actions[3]){actual[19]=3;actual[20]=0;actual[21]=0;} // The recorded native factory supplies the new circle.
 assert.deepEqual(actual,r.result,JSON.stringify(r.args));assert.equal(Boolean(actions[4]),r.retired);
 const events=[];if(actions[0])events.push([1,actions[0]]);if(actions[3]){events.push([2,7+actions[1]],[3,60,actual[18]],[4,actions[2],actual[3]]);}if(actions[5])events.push([5,actions[6]]);
 assert.deepEqual(events,r.events,JSON.stringify(r.args));}
for(const r of proof.hits){new Uint32Array(c.memory.buffer,c.input(),32).fill(0);new Uint32Array(c.memory.buffer,c.input(),r.args.length).set(r.args);assert.equal(c.hit(),1,JSON.stringify(r.args));const actual=Array.from({length:15},(_,i)=>c.hit_value(i)>>>0),actions=Array.from({length:4},(_,i)=>c.hit_action_value(i)>>>0);
 assert.deepEqual(actual,r.result,JSON.stringify(r.args));const events=[];if(actions[0])events.push([1,actions[0]]);if(actions[1])events.push([4,actions[1],actual[2]]);if(actions[2])events.push([5,actions[3]]);assert.deepEqual(events,r.events,JSON.stringify(r.args));}
for(const r of proof.slowdown)assert.equal(c.slowdown(...r.args)>>>0,r.result,JSON.stringify(r.args));
for(const r of proof.clocks)assert.equal(c.clock_rate(...r.args)>>>0,r.result,JSON.stringify(r.args));
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-shot-sakuya-verified.json'),JSON.stringify({passed:true,spawns:proof.spawns.length,updates:proof.updates.length,hits:proof.hits.length,slowdown:proof.slowdown.length,clocks:proof.clocks.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 452f30 allocation gate, 452ff0 aiming, attachment, explosion selection and child-driven radius/retirement, 453540 circle/rectangle attachment and timed damage, and 42c810 slowdown accumulation including boss scaling, cap and spell exceptions. Also records 84 native 424710 scoped ECL-rate samples and verifies the native global rate is restored. ANM immediate/pending interrupts, target selection/lookup, new circle allocation, sound and slowdown requests use recording boundaries. Common allocator teardown, Production ECL/ANM clock delivery, full gameplay and GPU pixels are separate.',sourceHashes:Object.fromEntries([...sources,'cpp/game/ShotManager.hpp','cpp/game/EnemyState.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))]))},null,2)+'\n');console.log(`PASS: ${proof.spawns.length} allocation gates / ${proof.updates.length} updates / ${proof.hits.length} hits / ${proof.slowdown.length} slowdown changes / ${proof.clocks.length} clocks.`);
