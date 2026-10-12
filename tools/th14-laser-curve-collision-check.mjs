import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-curve-collision-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-laser-curve-collision-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'curve-collision.wasm'),fixture='tests/cpp/th14-laser-curve-manager-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-collision-native.json'),'utf8')),p=c.allocate(256*32);
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,r.initial.length*8).set(r.initial.flat());
 assert.equal(c.collision(p,r.initial.length,r.width,r.rate,r.age,r.hit,r.probe),r.result,`collision ${i} result`);
 assert.deepEqual(Array.from({length:3},(_,j)=>c.value(j)>>>0),r.timer,`collision ${i} timer`);
 assert.deepEqual(Array.from({length:c.collision_count()},(_,j)=>Array.from({length:c.collision_size(j)},(_,k)=>c.collision_word(j,k)>>>0)),r.deliveries,`collision ${i} deliveries`);
}}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=[fixture,'cpp/game/LaserCurveTh14Runtime.cpp','cpp/game/LaserManager.cpp','cpp/game/LaserManager.hpp','cpp/game/LaserState.hpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail 440d80 segment collision midpoint/angle/width/length, distance gate >=16, graze selection/delivery, clock progression and 32x32 player-hit rectangle request, for 1/2/7/20 samples, rates .5/1/1.25, ordinary and warning probes. Player collision, graze and rectangle consumer are recorded boundaries. Polar unwritten scratch Z is controlled zero. Actual rectangle mutation, fragments, animation, whole update, real gameplay and pixels are outside this local proof.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-curve-collision-native.py','tools/th14-laser-curve-collision-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-laser-curve-collision-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} original curve collision cases.`);
