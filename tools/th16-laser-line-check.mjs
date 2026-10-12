import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/laser-line-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-laser-line-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
nativePython('tools/th16-laser-cut-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'line.wasm'),fixture='tests/cpp/th16-laser-line-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/laser-line-native.json'),'utf8')),p=c.allocate(0x358);let frames=0,deliveries=0;
const state=()=>Array.from({length:55},(_,j)=>c.value(j)>>>0);
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,r.request.length).set(r.request);c.initialize(p,r.rate);assert.deepEqual(state(),r.initial,`case ${i} initialize`);
 for(const [j,f] of r.frames.entries()){assert.equal(c.tick(),f.result,`case ${i} frame ${j} result`);assert.deepEqual(state(),f.state,`case ${i} frame ${j} state`);++frames;}
}}finally{c.release(p);}
for(const [i,r] of proof.cancellations.entries()){
 assert.equal(c.cancel(r.sprite,r.length,r.angle,r.mode),r.result,`cancel ${i} result`);assert.equal(c.value(0),r.state,`cancel ${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`cancel ${i} deliveries`);deliveries+=r.deliveries.length;
}
for(const [i,r] of proof.collisions.entries()){
 assert.equal(c.collision(...r.input),r.result,`collision ${i} result`);assert.deepEqual(Array.from({length:3},(_,j)=>c.value(19+j)>>>0),r.timer,`collision ${i} timer`);
 assert.deepEqual(Array.from({length:c.collision_count()},(_,j)=>Array.from({length:c.collision_size(j)},(_,k)=>c.collision_word(j,k)>>>0)),r.events,`collision ${i} events`);
}
let fragmentRequests=0,integratedFragments=0;
const cutProof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/laser-cut-native.json'),'utf8')),cutRequest=c.allocate(0x358);
try{for(const [rectangle,rows] of [[0,cutProof.circles],[1,cutProof.rectangles]])for(const [i,r] of rows.entries()){
 new Uint32Array(c.memory.buffer,cutRequest,214).set(r.request);
 assert.equal(rectangle?c.rectangle(cutRequest,...r.size,r.angle,r.mode):c.circle(cutRequest,r.radius,r.mode),r.result,`cut ${rectangle}/${i} result`);
 assert.deepEqual(Array.from({length:7},(_,j)=>c.circle_value(j)>>>0),r.state,`cut ${rectangle}/${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`cut ${rectangle}/${i} deliveries`);
 assert.deepEqual(Array.from({length:c.fragment_count()},(_,j)=>Array.from({length:214},(_,k)=>c.fragment_word(j,k)>>>0)),r.fragments,`cut ${rectangle}/${i} fragments`);fragmentRequests+=r.fragments.length;
 assert.equal(c.registry(cutRequest,r.radius||0,...(r.size||[0,0]),r.angle||0,r.mode,rectangle),r.result,`registry ${rectangle}/${i} result`);
 assert.deepEqual(Array.from({length:9},(_,j)=>c.registry_value(j)>>>0),[...r.state,1+r.fragments.length,0],`registry ${rectangle}/${i} state`);
 assert.equal(c.factory_count(),r.fragments.length,`registry ${rectangle}/${i} count`);
 for(const [j,f] of r.fragments.entries()){
  assert.deepEqual(Array.from({length:214},(_,k)=>c.factory_word(j,k)>>>0),f,`registry ${rectangle}/${i}/${j} request`);
  new Uint32Array(c.memory.buffer,cutRequest,214).set(f);c.initialize(cutRequest,1);const expected=state();expected[29]=0x10001+j;
  assert.deepEqual(Array.from({length:55},(_,k)=>c.factory_word(j,214+k)>>>0),expected,`registry ${rectangle}/${i}/${j} consumer`);++integratedFragments;
 }
}}finally{c.release(cutRequest);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-laser-line-verified.json'),JSON.stringify({passed:true,completeGame:false,initializations:proof.cases.length,frames,cancellations:proof.cancellations.length,deliveries,collisionCases:proof.collisions.length,circleCuts:cutProof.circles.length,rectangleCuts:cutProof.rectangles.length,fragmentRequests,integratedFragments,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own431b30 state initialization and432f40 motion through4333ae, ETEX1/4/8/16/80/100/400/800/1000/8000/10000/100000/80000000, clocks and434cd0 full cancellation. Native433510 collision geometry, graze projection/clocks and hit rectangle requests. ANM, sound, effects/rewards, player probe/hit and rectangle consumer controlled. Polar unwritten scratchZ controlled zero. Own434730 circles/433860 rotated rectangles and358-byte fragments also execute. Production fragment registry/initialization uses controlled blankANM. Effect/reward registration and pixel equivalence remain unverified; other ETEX and full game are not covered.',sourceHashes:Object.fromEntries([fixture,'cpp/game/LaserLineTh16.cpp','cpp/game/LaserCutTh16.cpp','cpp/game/LaserManager.cpp','cpp/game/LaserManager.hpp','cpp/game/LaserState.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 initializations, ${frames} motion frames, ${proof.cancellations.length} cancellations, ${proof.collisions.length} collision cases, ${cutProof.circles.length} circles, ${cutProof.rectangles.length} rectangles, ${integratedFragments} production fragments`);
