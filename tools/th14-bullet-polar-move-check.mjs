import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-polar-move-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-polar-move-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'bullet-polar-move.wasm'),fixture='tests/cpp/th14-bullet-polar-move-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-polar-move-native.json'),'utf8'));
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.duration,r.rate,r.angle,r.speed),0,`case ${i} canonical result`);
 const state=()=>Array.from({length:20},(_,j)=>c.word(j)>>>0);
 assert.deepEqual(state(),r.initial,`case ${i} initial`);c.add_flags();
 for(const [j,f] of r.frames.entries()){assert.equal(c.tick(),f.status,`case ${i}/${j} result`);assert.deepEqual(state(),f.state,`case ${i}/${j} state`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');const sources=[fixture,'cpp/game/BulletTh14.cpp','cpp/game/Movement.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Complete retail 418140 ETEX 80000 setup and 41a750 motion: active mask/index, position, scalar speed/angle, velocity, timer, polar slot fields, duration. Preserves native reset-to-zero timer and expiry mask FFFFFFF6. After setup, controlled active bits 1/8 exercise that mask. Durations -1/0 compare local motion only: they retain 80000 and cause native full-update retry to loop, so no full-update equivalence claim for those durations. Rates 0/.5/1/1.25 and explicit extreme angles compared. Animation, collision and pixels excluded',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-polar-move-native.py','tools/th14-bullet-polar-move-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-polar-move-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} original ETEX 80000 setup / 12-frame motion cases.`);
