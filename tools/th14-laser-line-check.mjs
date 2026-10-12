import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-line-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-laser-line-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-laser-line-collision-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'line.wasm'),fixture='tests/cpp/th14-laser-line-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-line-native.json'),'utf8')),p=c.allocate(0x374);let frames=0,deliveries=0;
const state=()=>Array.from({length:31},(_,j)=>c.value(j)>>>0);
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,r.request.length).set(r.request);c.initialize(p,r.rate);assert.deepEqual(state(),r.initial,`case ${i} initialize`);
 for(const [j,f] of r.frames.entries()){assert.equal(c.tick(),f.result,`case ${i} frame ${j} result`);assert.deepEqual(state(),f.state,`case ${i} frame ${j} state`);++frames;}
}}finally{c.release(p);}
for(const [i,r] of proof.cancellations.entries()){
 assert.equal(c.cancel(r.sprite,r.length,r.angle,r.mode),r.result,`cancel ${i} result`);assert.equal(c.value(0),r.state,`cancel ${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`cancel ${i} deliveries`);deliveries+=r.deliveries.length;
}
let fragmentRequests=0;
const circleRequest=c.allocate(0x354);
try{for(const [i,r] of proof.circles.entries()){
 new Uint32Array(c.memory.buffer,circleRequest,213).set(r.request);
 assert.equal(c.circle(circleRequest,r.radius,r.mode),r.result,`circle ${i} result`);
 assert.deepEqual(Array.from({length:7},(_,j)=>c.circle_value(j)>>>0),r.state,`circle ${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`circle ${i} deliveries`);
 assert.deepEqual(Array.from({length:c.fragment_count()},(_,j)=>Array.from({length:213},(_,k)=>c.fragment_word(j,k)>>>0)),r.fragments,`circle ${i} fragments`);fragmentRequests+=r.fragments.length;
}
for(const [i,r] of proof.rectangles.entries()){
 new Uint32Array(c.memory.buffer,circleRequest,213).set(r.request);
 assert.equal(c.rectangle(circleRequest,...r.size,r.angle,r.mode),r.result,`rectangle ${i} result`);
 assert.deepEqual(Array.from({length:7},(_,j)=>c.circle_value(j)>>>0),r.state,`rectangle ${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`rectangle ${i} deliveries`);
 assert.deepEqual(Array.from({length:c.fragment_count()},(_,j)=>Array.from({length:213},(_,k)=>c.fragment_word(j,k)>>>0)),r.fragments,`rectangle ${i} fragments`);fragmentRequests+=r.fragments.length;
}}finally{c.release(circleRequest);}
const sha=b=>createHash('sha256').update(b).digest('hex');
const collisionProof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-line-collision-native.json'),'utf8'));
for(const [i,r] of collisionProof.cases.entries()){
 assert.equal(c.collision(r.length,r.width,r.angle,r.rate,r.age,r.hit,r.probe),r.result,`collision ${i} result`);
 assert.deepEqual(Array.from({length:3},(_,j)=>c.value(19+j)>>>0),r.timer,`collision ${i} timer`);
 assert.deepEqual(Array.from({length:c.collision_count()},(_,j)=>Array.from({length:c.collision_size(j)},(_,k)=>c.collision_word(j,k)>>>0)),r.deliveries,`collision ${i} deliveries`);
}
for(const [i,r] of collisionProof.scales.entries()){
 assert.equal(c.scale_case(r.length,r.width,r.spriteWidth,r.spriteHeight,r.rate),r.result,`scale ${i} result`);
 assert.deepEqual(Array.from({length:5},(_,j)=>c.scale_value(j)>>>0),[...r.scale,...r.clock],`scale ${i} axes/clock`);
}
let integratedFragments=0;
const registryRequest=c.allocate(0x354);
try{for(const [rectangle,rows] of [[0,proof.circles],[1,proof.rectangles]])for(const [i,r] of rows.entries()){
 new Uint32Array(c.memory.buffer,registryRequest,213).set(r.request);
 assert.equal(c.registry(registryRequest,r.radius||0,...(r.size||[0,0]),r.angle||0,r.mode,rectangle),r.result,`registry ${rectangle}/${i} result`);
 assert.deepEqual(Array.from({length:9},(_,j)=>c.registry_value(j)>>>0),[...r.state,1+r.fragments.length,0],`registry ${rectangle}/${i} state`);
 assert.equal(c.factory_count(),r.fragments.length,`registry ${rectangle}/${i} count`);
 for(const [j,f] of r.fragments.entries()){
  assert.deepEqual(Array.from({length:213},(_,k)=>c.factory_word(j,k)>>>0),f,`registry ${rectangle}/${i}/${j} request`);
  new Uint32Array(c.memory.buffer,registryRequest,213).set(f);c.initialize(registryRequest,1);const expected=state();expected[29]=0x10001+j;
  assert.deepEqual(Array.from({length:31},(_,k)=>c.factory_word(j,213+k)>>>0),expected,`registry ${rectangle}/${i}/${j} consumer`);++integratedFragments;
 }
}}finally{c.release(registryRequest);}
const report={passed:true,completeGame:false,initializations:proof.cases.length,frames,cancellations:proof.cancellations.length,deliveries,circleCuts:proof.circles.length,rectangleCuts:proof.rectangles.length,fragmentRequests,integratedFragments,registryCases:proof.circles.length+proof.rectangles.length,collisionCases:collisionProof.cases.length,scaleCases:collisionProof.scales.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 43aca0 state initialization, 43b060 ETEX 80/400/800/8000/10000/100000 and 43be20 growth/motion/offscreen retirement through 43c179, native clocks and 43da10 full cancel. Retail 43d300 circle and 43c500 rotated rectangle selection, retained-parent position/length/offset/mark and complete kind-0 fragment requests. Retail 43c250 geometry/graze clocks and player-hit rectangle request. ANM, sound, effects/items, player collision/graze and the player-hit rectangle consumer are recorded boundaries. Polar unwritten scratch Z is controlled zero. Production circle/rectangle registry integrations run real kind-0 constructors under controlled blank ANM scripts and compare every request and initial state. Full retail 43be20 entry also compares sprite width/height scale axes and the motion clock with recorded collision and ANM boundaries. Transform movement, real animation/update/draw sequencing and pixels remain outside this comparison.',sourceHashes:Object.fromEntries([fixture,'cpp/game/LaserLineTh14.cpp','cpp/game/LaserManager.cpp','cpp/game/LaserManager.hpp','cpp/game/LaserState.hpp','cpp/game/EnemyTh14Commands.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-line-native.py','tools/th14-laser-line-collision-native.py','tools/th14-laser-line-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-laser-line-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} initializations, ${frames} lifecycle frames, ${proof.cancellations.length} cancellations, ${deliveries} deliveries, ${report.circleCuts} circles, ${report.rectangleCuts} rectangles, ${fragmentRequests} fragment requests, ${report.collisionCases} collision cases, ${report.scaleCases} scale/clock cases, ${integratedFragments} production fragment consumers.`);
