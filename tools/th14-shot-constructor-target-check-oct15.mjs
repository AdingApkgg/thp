import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-constructor-target-check-oct15');
assert(!existsSync(out));mkdirSync(out);
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['tests/cpp/th14-shot-constructor-target-fixture.cpp','cpp/game/ShotSakuyaTh14.cpp','cpp/game/Movement.cpp'];
const bindings=Object.fromEntries([...sources,'tests/cpp/th14-shot-sakuya-fixture.cpp','cpp/game/ShotManager.hpp','cpp/game/EnemyState.hpp'].map(n=>[n,sha(read(resolve(rt,n)))]));
const wasm=resolve(out,'probe.wasm');
execFileSync(resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},windowsHide:true,stdio:'inherit'});
const bytes=read(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const nativeBytes=read(resolve(root,'artifacts/th14/shot-constructor-target-native-oct15.json')),native=JSON.parse(nativeBytes);
for(const row of native.cases){
 new Uint32Array(c.memory.buffer,c.input(),32).fill(0);new Uint32Array(c.memory.buffer,c.input(),row.args.length).set(row.args);
 assert.equal(c.constructor_hit(),1);assert.deepEqual(Array.from({length:15},(_,i)=>c.hit_value(i)>>>0),row.result,JSON.stringify(row.args));
 const actions=Array.from({length:4},(_,i)=>c.hit_action_value(i)>>>0),actual=c.hit_value(2)>>>0,events=[];
 if(actions[0])events.push([1,actions[0]]);if(actions[1])events.push([4,actions[1],actual]);if(actions[2])events.push([5,actions[3]]);
 assert.deepEqual(events,row.events,JSON.stringify(row.args));
}
// Reuse the immutable original callback corpus without overwriting its proof.
const priorBytes=read(resolve(root,'artifacts/th14/shot-sakuya-native.json')),prior=JSON.parse(priorBytes);
for(const row of prior.spawns){assert.equal(c.spawn(...row.args),Number(row.accepted));assert.deepEqual(Array.from({length:12},(_,i)=>c.value(i)>>>0),row.result);}
for(const row of prior.hits){new Uint32Array(c.memory.buffer,c.input(),32).fill(0);new Uint32Array(c.memory.buffer,c.input(),row.args.length).set(row.args);assert.equal(c.hit(),1);assert.deepEqual(Array.from({length:15},(_,i)=>c.hit_value(i)>>>0),row.result);}
for(const row of prior.updates){
 new Uint32Array(c.memory.buffer,c.input(),22).set(row.args);assert.equal(c.update(),1);
 const actual=Array.from({length:27},(_,i)=>c.update_value(i)>>>0),actions=Array.from({length:7},(_,i)=>c.action_value(i)>>>0);
 if(actions[3]){actual[19]=3;actual[20]=0;actual[21]=0;}
 assert.deepEqual(actual,row.result);assert.equal(Boolean(actions[4]),row.retired);
}
const result={passed:true,nativeHitCases:native.cases.length,unlinkedConstructorCases:native.cases.filter(r=>r.args[8]===2).length,
 priorSpawnCases:prior.spawns.length,priorHitCases:prior.hits.length,priorUpdateCases:prior.updates.length,
 nativeExecutableSha256:native.executableSha256,nativeReceiptSha256:sha(nativeBytes),priorNativeCorpusSha256:sha(priorBytes),
 sourceHashes:bindings,wasmSha256:sha(bytes),toolSha256:sha(read(import.meta.filename)),completeGame:false,nativeEquivalent:false,
 scope:'Original 453540 raw result words and recorded requests for linked, null and live unlinked hit receivers. Existing original callback corpus replayed without changing its files. This verifies callbacks; full recording, physical graphics/audio and complete-game fidelity remain separate.'};
writeFileSync(resolve(out,'receipt.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
writeFileSync(resolve(root,'docs/porting/th14-shot-constructor-target-verified-oct15.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,nativeHitCases:result.nativeHitCases,unlinkedConstructorCases:result.unlinkedConstructorCases,priorSpawnCases:result.priorSpawnCases,priorHitCases:result.priorHitCases,priorUpdateCases:result.priorUpdateCases}));
