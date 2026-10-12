import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-spread-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-shot-spread-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-shot-spread-fixture.cpp','cpp/game/ShotCallbacksTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'spread.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-spread-native.json'),'utf8'));
for(const r of proof.spawns){c.spawn(...r.args);assert.deepEqual(Array.from({length:6},(_,i)=>c.spawn_value(i)>>>0),r.result,JSON.stringify(r.args));}
for(const r of proof.updates){c.update(...r.args);assert.deepEqual([0,1].map(i=>c.update_value(i)>>>0),r.result,JSON.stringify(r.args));}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-shot-spread-verified.json'),JSON.stringify({passed:true,spawns:proof.spawns.length,updates:proof.updates.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 452c10 spread spawn with actual visual RNG and 452e00 per-invocation active-shot acceleration. Compares angle wrapping at +/-pi, flags mask, visual RNG state/call count, untouched script RNG, state 0/1/2 and frozen/advanced clocks at rates 0/.5/1/1.25. Actual shot spawning, hit callback 4, area ownership, render and complete gameplay are separate.',sourceHashes:Object.fromEntries([...sources,'cpp/game/ShotManager.hpp','cpp/game/Rng.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-shot-spread-native.py','tools/th14-shot-spread-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');console.log(`PASS: ${proof.spawns.length} spread spawns and ${proof.updates.length} accelerating updates.`);
