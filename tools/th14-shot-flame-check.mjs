import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-flame-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-shot-flame-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-shot-flame-fixture.cpp','cpp/game/ShotCallbacksTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'flame.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-flame-native.json'),'utf8'));
for(const r of proof.spawns){c.spawn(...r.args);assert.deepEqual(Array.from({length:4},(_,i)=>c.spawn_value(i)>>>0),r.result,JSON.stringify(r.args));}
for(const r of proof.updates){const interrupt=c.update(...r.args);assert.deepEqual(Array.from({length:5},(_,i)=>c.value(i)>>>0),r.result,JSON.stringify(r.args));assert.deepEqual(interrupt?[1]:[],r.events,JSON.stringify(r.args));}
for(const r of proof.small){const interrupt=c.small(...r.args);assert.deepEqual([0,1].map(i=>c.small_value(i)>>>0),r.result,JSON.stringify(r.args));assert.deepEqual(interrupt?[1]:[],r.events,JSON.stringify(r.args));}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-shot-flame-verified.json'),JSON.stringify({passed:true,spawns:proof.spawns.length,updates:proof.updates.length,smallUpdates:proof.small.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 452d20 spread without flag clearing, 452ca0 per-invocation slowing, age/flag-gated visual RNG sampling and area damage halving, and 452da0 slowing/age-3 interrupt independent of state/timer advancement. ANM interrupt delivery and the common update that subsequently copies shot damage are separate. No full-game claim.',sourceHashes:Object.fromEntries([...sources,'cpp/game/ShotManager.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))]))},null,2)+'\n');console.log(`PASS: ${proof.spawns.length} spawns / ${proof.updates.length} updates / ${proof.small.length} small-flame updates.`);
