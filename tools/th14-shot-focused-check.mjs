import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-focused-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-shot-focused-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'focused.wasm'),fixture='tests/cpp/th14-shot-focused-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-focused-native.json'),'utf8')),p=c.allocate(60),f=v=>{const a=new Float32Array([v]);return new Uint32Array(a.buffer)[0];};
const state=()=>Array.from({length:20},(_,j)=>c.value(j)>>>0);
for(const [i,r] of proof.spawns.entries()){assert.equal(c.spawn(r.power,r.flags,...r.targetPosition),1,`spawn ${i}`);assert.deepEqual(state(),r.result,`spawn ${i} state`);}
try{for(const [i,r] of proof.updates.entries()){
 new Uint32Array(c.memory.buffer,p,15).set([r.power,r.flags,...r.targetPosition.map(f),f(r.rate),r.age,r.decay,r.steering,r.focused,r.firing,r.blocked,r.life,r.target,r.cached,r.bomb]);
 assert.equal(c.update(p),r.interrupts.length?1:0,`update ${i} status`);assert.deepEqual(state(),r.result,`update ${i} state`);
}}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-shot-focused-verified.json'),JSON.stringify({passed:true,spawns:proof.spawns.length,updates:proof.updates.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'451af0 spawn callback 2 and 451cd0 update callback 2 field writes. Actual retail nearest/id/flag checks, atan2, angle wrapping and timer operations; ANM lookup/interrupt are boundaries. Compares target/id, angle/speed, area flags/radius/growth, decay/steering clocks, VM flags/scales, state, shared cached power and damage; global Bomb states 0/1/2 and dialogue/life gates are included. Production connects normalized area parameters; separate hit/damage/reward reports cover those consumers. Native area allocation, generic shot lifecycle, other raw shot callbacks and full gameplay remain unverified.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh14.cpp','cpp/game/ShotManager.cpp','cpp/game/ShotManager.hpp','cpp/game/PlayerFrame.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-shot-focused-native.py','tools/th14-shot-focused-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.spawns.length} focused spawns, ${proof.updates.length} focused updates.`);
