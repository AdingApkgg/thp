import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-infinite-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-laser-infinite-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-laser-infinite-collision-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'infinite.wasm'),fixture='tests/cpp/th14-laser-infinite-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-infinite-native.json'),'utf8')),p=c.allocate(0x374);let frames=0,deliveries=0;
const state=()=>Array.from({length:19},(_,j)=>c.value(j)>>>0);
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,r.request.length).set(r.request);c.initialize(p,r.rate);assert.deepEqual(state(),r.initial,`case ${i} initialize`);
 for(const [j,f] of r.frames.entries()){assert.equal(c.tick(),f.result,`case ${i} frame ${j} result`);assert.deepEqual(state(),f.state,`case ${i} frame ${j} state`);++frames;}
}}finally{c.release(p);}
for(const [i,r] of proof.cancellations.entries()){
 assert.equal(c.cancel(r.sprite,r.length,r.angle,r.mode),r.result,`cancel ${i} result`);assert.equal(c.value(0),r.state,`cancel ${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`cancel ${i} deliveries`);deliveries+=r.deliveries.length;
}
let fragmentRequests=0;
for(const [i,r] of proof.circles.entries()){
 assert.equal(c.circle(r.sprite,r.length,r.angle,r.radius,r.mode),r.result,`circle ${i} result`);assert.equal(c.value(6)>>>0,r.newLength,`circle ${i} length`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`circle ${i} deliveries`);
 assert.deepEqual(Array.from({length:c.fragment_count()},(_,j)=>Array.from({length:0x354/4},(_,k)=>c.fragment_word(j,k)>>>0)),r.fragments,`circle ${i} fragments`);fragmentRequests+=r.fragments.length;
}
let rectangleFragments=0;
for(const [i,r] of proof.rectangles.entries()){
 assert.equal(c.rectangle(r.sprite,r.length,r.angle,r.width,r.height,r.rotation,r.mode,r.flags,r.placement),r.result,`rectangle ${i} result`);assert.equal(c.value(6)>>>0,r.newLength,`rectangle ${i} length`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`rectangle ${i} deliveries`);
 assert.deepEqual(Array.from({length:c.fragment_count()},(_,j)=>Array.from({length:0x354/4},(_,k)=>c.fragment_word(j,k)>>>0)),r.fragments,`rectangle ${i} fragments`);rectangleFragments+=r.fragments.length;
}
let integratedFragments=0;
for(const [i,r] of proof.rectangles.entries()){
 assert.equal(c.registry_rectangle(r.sprite,r.length,r.angle,r.width,r.height,r.rotation,r.mode,r.flags,r.placement),r.result,`registry ${i} result`);
 assert.deepEqual(Array.from({length:3},(_,j)=>c.registry_value(j)>>>0),[r.newLength,1+r.fragments.length,0],`registry ${i} state`);
 assert.deepEqual(Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:4},(_,k)=>c.delivery_word(j*4+k)>>>0)),r.deliveries,`registry ${i} deliveries`);
 assert.equal(c.factory_count(),r.fragments.length,`registry ${i} count`);
 for(const [j,f] of r.fragments.entries()){
  assert.deepEqual(Array.from({length:213},(_,k)=>c.factory_word(j,k)>>>0),f,`registry ${i}/${j} request`);
  assert.deepEqual(Array.from({length:10},(_,k)=>c.factory_word(j,213+k)>>>0),[0,2,...f.slice(0,3),f[3],f[5],f[7],f[8],0x10001+j],`registry ${i}/${j} initial state`);++integratedFragments;
 }
}
const collisionProof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-infinite-collision-native.json'),'utf8'));
for(const [i,r] of collisionProof.cases.entries()){
 assert.equal(c.collision(r.length,r.width,r.angle,r.rate,r.age,r.hit,r.probe,r.state),r.result,`collision ${i} result`);
 assert.deepEqual(Array.from({length:3},(_,j)=>c.collision_timer(j)>>>0),r.timer,`collision ${i} timer`);
 assert.deepEqual(Array.from({length:c.collision_count()},(_,j)=>Array.from({length:c.collision_size(j)},(_,k)=>c.collision_word(j,k)>>>0)),r.deliveries,`collision ${i} deliveries`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-laser-infinite-verified.json'),JSON.stringify({passed:true,initializations:proof.cases.length,frames,cancellations:proof.cancellations.length,deliveries,circleCuts:proof.circles.length,fragmentRequests,rectangleCuts:proof.rectangles.length,rectangleFragments,integratedFragments,registryCases:proof.rectangles.length,collisionCases:collisionProof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 43ddc0 state initialization, 43fd20 ETEX 80/400/100000 and 43e040 motion/lifecycle up to 43e27c; native timer increments. Retail 43f8f0 full cancellation including recorded effect/item deliveries. ANM binding/update, sound, effect allocation and item creation are boundaries. Retail 43f220 circular sampling/cut length and complete kind-0 fragment requests are compared; Retail 43e500 rectangular splitting compares count, retained length, effect/item deliveries and every byte of kind-0 fragment requests. Production sends both cut shapes to the kind-0 constructor; Real manager registry and kind-0 constructors run under controlled blank ANM scripts and compare every request, initial position/angle/length/width/speed/id, retained parent, active count and deliveries. Real animation scripts, later child lifecycle and pixels remain outside. Retail 43e300 collision geometry, graze clocks and 32x32 player-hit cut request are compared with collision/graze/rectangle consumer recorded boundaries. Warning steering, native resource ANM execution and pixels are outside this comparison. Negative externally seeded transform masks are refused.',sourceHashes:Object.fromEntries([fixture,'cpp/game/LaserInfiniteTh14.cpp','cpp/game/LaserManager.cpp','cpp/game/LaserManager.hpp','cpp/game/LaserState.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-infinite-native.py','tools/th14-laser-infinite-collision-native.py','tools/th14-laser-infinite-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} initializations, ${frames} lifecycle frames, ${proof.cancellations.length} cancellations, ${deliveries} deliveries, ${proof.circles.length} circle cuts / ${fragmentRequests} fragment requests, ${proof.rectangles.length} rectangle cuts / ${rectangleFragments} fragment requests / ${integratedFragments} production fragment consumers, ${collisionProof.cases.length} collision cases.`);
