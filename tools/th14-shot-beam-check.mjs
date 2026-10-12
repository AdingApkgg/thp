import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-beam-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-shot-beam-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-shot-beam-fixture.cpp','cpp/game/ShotCallbacksTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'beam.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-beam-native.json'),'utf8'));
for(const r of proof.spawns){c.spawn(...r.args);assert.deepEqual(Array.from({length:4},(_,i)=>c.spawn_value(i)>>>0),r.result,JSON.stringify(r.args));assert.deepEqual(r.events,[['sound',20,new Uint32Array(new Float32Array([r.args[1]]).buffer)[0]]]);}
for(const r of proof.rows){assert.equal(c.update(...r.args),1);assert.deepEqual(Array.from({length:18},(_,i)=>c.value(i)>>>0),r.result,JSON.stringify(r.args));const e=[];if(c.event_value(0))e.push(['pan',c.event_value(1)>>>0]);if(c.event_value(2))e.push(['interrupt',c.event_value(2)]);if(c.event_value(3))e.push(['stop',20]);assert.deepEqual(e,r.events,JSON.stringify(r.args));}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-shot-beam-verified.json'),JSON.stringify({passed:true,spawns:proof.spawns.length,updates:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 4523a0/4523f0 beam spawn/update, fixed-point option origin, angle normalization, per-invocation length, separate area center, sprite-size and texture-scale writes, current-voice pan, each retirement gate, hit interrupt transition and missing VM. Native libm and polar helper execute. ANM lookup/interrupt and DirectSound delivery are controlled boundaries. Hit callback, common movement, production audio and complete gameplay are separate.',sourceHashes:Object.fromEntries([...sources,'cpp/game/ShotManager.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))]))},null,2)+'\n');console.log(`PASS: ${proof.spawns.length} beam spawns and ${proof.rows.length} updates.`);
