import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-child-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-child-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'child.wasm'),fixture='tests/cpp/th14-bullet-child-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-child-native.json'),'utf8')),p=c.allocate(0x318);let requests=0;
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,198).set(r.program);assert.equal(c.run(p,r.index,r.active),0,`case ${i} result`);
 assert.deepEqual(Array.from({length:3},(_,j)=>c.value(j)>>>0),r.result,`case ${i} parent`);
 assert.deepEqual(Array.from({length:c.request_count()},(_,j)=>Array.from({length:224},(_,k)=>c.request_word(j,k)>>>0)),r.requests,`case ${i} requests`);requests+=r.requests.length;
}}finally{c.release(p);}
let poolCases=0,capacityCases=0;
const checkPool=(count,layers,angle,speed,cancel,rate,filled)=>{
 const label=`pool ${count}/${layers}/${angle}/${speed}/${cancel}/${rate}/${filled}`;
 assert.equal(c.pool(count,layers,angle,speed,cancel,rate,filled),0,label);
 assert.deepEqual(Array.from({length:7},(_,j)=>c.pool_value(j)>>>0),[Math.min(2000,filled+1+count*layers),Math.min(count*layers,1999-filled),0,cancel?4:1,2,0,1],label);
 ++poolCases;if(filled)++capacityCases;
};
for(const count of [1,3,7])for(const layers of [1,2,4])for(const angle of [-1000,-998,-997.5,.37,200])for(const speed of [-1000,-998,-997.5,3.25])for(const cancel of [0,1])for(const rate of [0,.5,1,1.25])checkPool(count,layers,angle,speed,cancel,rate,0);
for(const filled of [1998,1999])for(const cancel of [0,1])for(const rate of [0,.5,1,1.25])checkPool(3,2,.37,3.25,cancel,rate,filled);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-bullet-child-verified.json'),JSON.stringify({passed:true,completeGame:false,cases:proof.cases.length,requests,poolCases,capacityCases,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 418140 ETEX 2000 paired-record dispatch, active/concurrent gating, exact 0x380 child emitter bytes, copied 18-record program, angle/speed sentinels, angle normalization, parent index and optional cancellation request. Child emission and parent cancellation are recorded boundaries; their launch/cancel behavior has separate proofs. Separately exercises the production child factory with controlled blank ANM, checking emitted child state and parent cancellation, including exhausted/one-slot-free pools. These integration cases are not native pool/recursion comparisons. Recursive ordering, whole-frame movement, animation and pixels remain outside this comparison.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletState.hpp','cpp/game/BulletManager.hpp','cpp/game/BulletManager.cpp','cpp/game/BulletTh14Launch.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-child-native.py','tools/th14-bullet-child-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} ETEX 2000 cases / ${requests} child requests; ${poolCases} production pool cases (${capacityCases} capacity cases).`);
