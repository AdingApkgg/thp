import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/camera-check');
mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-stage-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/StageScript.cpp','cpp/game/StageResource.cpp','cpp/game/SceneCamera.cpp','cpp/game/GraphicsMath.cpp','cpp/game/Interpolation.cpp','cpp/game/FogInterpolation.cpp','cpp/game/Movement.cpp','tests/cpp/th14-camera-fixture.cpp'],wasm=resolve(out,'cameras.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/stage-native.json'),'utf8'));
const begin=(code,rate)=>{const b=Buffer.from(code,'hex'),p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);assert.equal(c.begin(p,b.length,rate),1);c.release(p);};
const compare=(expected,label)=>{
 expected.values.forEach((v,i)=>assert.ok(Math.abs(c.value(i)-v)<=Math.max(2e-5,Math.abs(v)*2.4e-7),`${label} component ${i}: ${c.value(i)} != ${v}`));
 expected.integers.forEach((v,i)=>assert.equal(c.integer(i)>>>0,v,`${label} integer ${i}`));
};
for(const row of proof.rows){begin(row.code,row.rate);for(const [frame,expected] of row.timeline.entries()){assert.equal(c.tick(),1,`${row.name} ${frame}`);compare(expected,`${row.name} rate ${row.rate} frame ${frame}`);}}
for(const row of proof.effects){begin('0000000000000800',row.rate);c.effect(row.kind,row.frame);assert.equal(c.tick(),1);compare(row.output,`effect ${row.kind} rate ${row.rate} frame ${row.frame}`);}
for(const row of proof.views){const p=c.allocate(160),v=new Float32Array(c.memory.buffer,p,40);v.set(row.input);v.set(row.output.lookAt.flat(),16);v.set(row.output.perspective,28);c.view_begin(p);assert.equal(c.view_matches(p+64,p+112),1,JSON.stringify(row));c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'Seven retail STD camera timelines at three rates and camera-effect states. ANM creation, object interrupts and deformation allocation are sinks; rendering, culling and complete gameplay remain separate.',
 nativeExecutableSha256:proof.executableSha256,retailTimelines:proof.rows.length,retailFrames:proof.rows.reduce((n,r)=>n+r.timeline.length,0),effectStates:proof.effects.length,cameraArgumentCases:proof.views.length,
 resourceHashes:Object.fromEntries(proof.rows.map(r=>[r.name,r.sha256])),wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/Stage.hpp','cpp/game/SceneCamera.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-stage-native.py','tools/th14-camera-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-camera-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.retailFrames} retail TH14 STD camera frames and ${report.effectStates} effect states.`);
