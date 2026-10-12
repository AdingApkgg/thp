import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/player-scale-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-player-scale-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'scale.wasm'),fixture='tests/cpp/th14-player-scale-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,p=c.allocate(56);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/player-scale-native.json'),'utf8'));
try{
 for(const r of proof.requests){new Uint32Array(c.memory.buffer,p,14).set(r.initial);c.request(p,r.value);assert.deepEqual(Array.from({length:14},(_,i)=>c.value(i)>>>0),r.result,JSON.stringify(r));const value=new DataView(new Uint32Array([r.value]).buffer).getFloat32(0,true);const enabled=!(value<=1);assert.deepEqual(r.events,Array.from({length:16},(_,i)=>[i+1,enabled?3:2]).concat(enabled?[]:[['rebuild']]));}
 for(const r of proof.updates){new Uint32Array(c.memory.buffer,p,14).set(r.initial);c.update(p,r.speed,r.frame);assert.deepEqual(Array.from({length:14},(_,i)=>c.value(i)>>>0),r.result,JSON.stringify(r));assert.deepEqual(Array.from({length:3},(_,i)=>c.visual_value(i)>>>0),r.visual,JSON.stringify(r));assert.deepEqual(Array.from({length:24},(_,i)=>c.bounds_value(i)>>>0),r.bounds,JSON.stringify(r));}
}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/PlayerFrame.cpp','cpp/game/PlayerFrame.hpp','cpp/game/EnemyCallbacks.cpp','cpp/game/EnemyCallbacks.hpp','cpp/game/GameBattle.hpp','cpp/game/EnemyTh14Commands.cpp'];
writeFileSync(resolve(root,'docs/porting/th14-player-scale-verified.json'),JSON.stringify({passed:true,requestCases:proof.requests.length,updateCases:proof.updates.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 4504c0 scale request, 44c270/4358e0 option interrupt delivery (47f140 and option rebuild 44f970 are controlled boundaries), and 44e1b4..44e8d5 body scale/blink, real 414140 interpolation and four XYZ collision/pickup regions. Flags, timer pointer preservation, 120-frame SSE interpolation and completed-duration behavior are compared bitwise. Infinity/NaN request handling is included. Full option recreation, projectile scaling, circular-hit scaling, death/stage resets and complete player lifecycle remain unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-player-scale-native.py','tools/th14-player-scale-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.requests.length} player scale requests; ${proof.updates.length} body/bounds updates.`);
