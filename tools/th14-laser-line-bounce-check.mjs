import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-line-bounce-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-laser-line-bounce-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'bounce.wasm'),fixture='tests/cpp/th14-laser-line-bounce-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-line-bounce-native.json'),'utf8')),p=c.allocate(0x354);
const state=()=>Array.from({length:231},(_,j)=>c.value(j)>>>0),requests=()=>Array.from({length:c.request_count()},(_,j)=>Array.from({length:213},(_,k)=>c.request_word(j,k)>>>0));let deliveries=0;
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,213).set(r.request);assert.equal(c.initialize(p,r.rate),0,`case ${i} setup result`);assert.deepEqual(state(),r.initial,`case ${i} setup`);
 assert.equal(c.tick(),r.result,`case ${i} result`);assert.deepEqual(state(),r.state,`case ${i} state`);assert.deepEqual(requests(),r.requests,`case ${i} requests`);deliveries+=r.requests.length;
 assert.equal(c.full_tick(),r.fullResult,`case ${i} full result`);assert.deepEqual(state(),r.fullState,`case ${i} full state`);assert.deepEqual(requests(),r.fullRequests,`case ${i} full requests`);
 assert.equal(c.registry(p,r.rate),r.fullResult,`case ${i} registry result`);assert.deepEqual(state(),r.fullState,`case ${i} registry state`);assert.deepEqual(requests(),r.fullRequests,`case ${i} factory requests`);
 assert.deepEqual([c.registry_value(0),c.registry_value(1)],[1+r.fullRequests.length,0],`case ${i} registry count/error`);
 for(const [j,f] of r.fullRequests.entries())assert.deepEqual(Array.from({length:9},(_,k)=>c.child_value(j,k)>>>0),[f[0],f[1],f[2],f[3],f[8],f[5],f[7],0,0],`case ${i} child ${j} initial state`);
}}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-laser-line-bounce-verified.json'),JSON.stringify({passed:true,completeGame:false,cases:proof.cases.length,requests:deliveries,registryCases:proof.cases.length,integratedChildren:deliveries,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 43b060 ETEX 40 setup/mutated program, 43b730 tip-bound bounce with actual 4055e0 finite-segment intersection, reflection, complete 0x354 child requests and active completion. Also 43be20 state/motion sequencing through 43c179. Factory and sound are recorded boundaries; factory returns zero deliberately. Separately compares actual production registry factory consumption, parent state, every child request and initial state under controlled blank ANM. Native registry traversal/capacity, ANM, collisions, future child bounces and GPU pixels remain outside this comparison.',sourceHashes:Object.fromEntries([fixture,'cpp/game/LaserLineTh14.cpp','cpp/game/LaserState.hpp','cpp/game/LaserManager.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-line-bounce-native.py','tools/th14-laser-line-bounce-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} laser bounce setup/tick/frame cases and ${deliveries} child requests.`);
