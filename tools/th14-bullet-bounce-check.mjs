import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-bounce-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-bounce-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th14-bullet-bounce-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-bounce-native.json'),'utf8'));
const state=()=>Array.from({length:19},(_,n)=>c.word(n)>>>0);
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.override,r.mask,r.x,r.y,r.angle,r.speed,r.limit),0,`setup ${i}`);assert.deepEqual(state(),r.initial,`setup state ${i}`);
 for(const [j,f] of r.frames.entries()){assert.equal(c.tick(),f.status,`case ${i} frame ${j} return`);assert.deepEqual(state(),f.state,`case ${i} frame ${j} state`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');const report={passed:true,initializations:proof.cases.length,frames:proof.cases.length*2,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail ETEX 0x40 setup 418140 and bounce 41a1a0 with real four wall consumers 419d90/419ed0/41a000/41a0d0. All 64 wall/control masks, ordinary/custom/manager override bounds, exact edge inclusion, corners, large angles, retained fields, speed sentinels, bounce counts and single sound per update. Sound is controlled. Complete scheduling, collisions, animation and GPU pixels remain outside this helper proof.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletTh14.hpp','cpp/game/BulletState.hpp','cpp/game/Movement.cpp','cpp/game/Timer.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-bounce-native.py','tools/th14-bullet-bounce-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-bounce-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.initializations} ETEX 0x40 setups / ${report.frames} motion frames.`);
