import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-acceleration-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-acceleration-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th14-bullet-acceleration-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-acceleration-native.json'),'utf8'));
const state=()=>Array.from({length:17},(_,n)=>c.word(n)>>>0);
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.index,r.duration,r.rate,r.angle,r.acceleration),0,`setup ${i}`);assert.deepEqual(state(),r.initial,`setup state ${i}`);
 for(const [j,f] of r.frames.entries()){assert.equal(c.tick(),f.status,`case ${i} frame ${j} return`);assert.deepEqual(state(),f.state,`case ${i} frame ${j} state`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');const report={passed:true,initializations:proof.cases.length,frames:proof.cases.length*96,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail ETEX 4 setup 418140 and motion 419560, including real 44ee00 aim, 407170 angle normalization, 41bf40 polar, native atan2/sqrt and timer. Fixed acceleration vector, current-angle/aim sentinels, retained vector Z, zero/negative/one/60-frame durations, three rates, scalar speed then vector-derived speed and direction. Sound delivery is controlled. This helper proof does not verify full concurrent-transform scheduling, animation, gameplay collisions or complete trajectories.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletTh14.hpp','cpp/game/BulletState.hpp','cpp/game/Movement.cpp','cpp/game/Timer.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-acceleration-native.py','tools/th14-bullet-acceleration-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-acceleration-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.initializations} ETEX 4 setups / ${report.frames} motion frames.`);
