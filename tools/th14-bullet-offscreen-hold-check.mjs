import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-offscreen-hold-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-offscreen-hold-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'hold.wasm'),fixture='tests/cpp/th14-bullet-offscreen-hold-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-offscreen-hold-native.json'),'utf8'));
const state=()=>Array.from({length:6},(_,j)=>c.value(j)>>>0);
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.initialize(...r.position,r.angle,...r.dimension,r.count,r.early,r.rate),0,`case ${i} setup result`);assert.deepEqual(state(),r.initial,`case ${i} setup`);
 assert.equal(c.tick(),r.result,`case ${i} result`);assert.deepEqual(state(),r.state,`case ${i} state`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-bullet-offscreen-hold-verified.json'),JSON.stringify({passed:true,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,normalizerDllSha256:proof.normalizerDllSha256,normalizerAddress:proof.normalizerAddress,wasmSha256:sha(bytes),scope:'Actual retail 418140 ETEX 100 setup and 41a830 countdown, unscaled sprite visibility, four expanded corners, directional early completion and active-bit retirement. Native comparison executes pinned D3DX9_43 SSE normalization with controlled CPU-dispatch selection. Only resulting state is compared, not every normalization float or other CPU profiles. Whole-frame culling/order, animation and GPU pixels remain outside this comparison.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-offscreen-hold-native.py','tools/th14-bullet-offscreen-hold-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} ETEX 100 setup/consumer cases.`);
