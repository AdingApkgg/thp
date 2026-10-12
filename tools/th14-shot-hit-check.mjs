import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-hit-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-shot-hit-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'hit.wasm'),fixture='tests/cpp/th14-shot-hit-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-hit-native.json'),'utf8')),p=c.allocate(28),f=v=>{const a=new Float32Array([v]);return new Uint32Array(a.buffer)[0];};
let active=0;
try{for(const [i,r] of proof.rows.entries()){
 new Uint32Array(c.memory.buffer,p,7).set([r.age,r.advanced,r.power,r.seed,f(r.radius),f(r.angle),f(r.speed)]);assert.equal(c.run(p),1,`callback ${i}`);
 assert.deepEqual(Array.from({length:14},(_,j)=>c.value(j)>>>0),r.result,`callback ${i} state`);
 if(r.result[8]){++active;assert.deepEqual(r.events,[['interrupt',3],['effect',149,0xffffffff,0,0],['sound',68,f(17)]],`callback ${i} requests`);}else assert.deepEqual(r.events,[]);
}}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-shot-hit-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,activeHits:active,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 452050 callback 1 gate, actual RNG/polar/angle math, speed writes, decay reset, focused-hit counter and damage return. Records interrupt 3, effect 149 arguments and sound 68 boundaries; native scratch stack initialized to zero (polar writes X/Y only). Production allocation/rendering/sound and the damage-area collector are outside this proof.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh14.cpp','cpp/game/ShotManager.hpp','cpp/game/Rng.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-shot-hit-native.py','tools/th14-shot-hit-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.rows.length} focused hit callbacks, ${active} active hits.`);
