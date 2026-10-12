import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-size-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-size-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th14-bullet-size-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-size-native.json'),'utf8'));
const state=()=>Array.from({length:14},(_,n)=>c.word(n)>>>0);
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.mode,r.duration,r.rate,r.start,r.target),0,`setup ${i}`);assert.deepEqual(state(),r.initial,`setup state ${i}`);
 for(const [j,f] of r.frames.entries()){c.tick();assert.deepEqual(state(),f,`case ${i} frame ${j} state`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');const report={passed:true,initializations:proof.cases.length,frames:proof.cases.length*96,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail ETEX 400000 setup 418140 and unmodified size update block 416781..4167c4, including real 414140 interpolation and 4041a0 easing: all 32 modes, three rates, zero/negative/one/30-frame durations, three endpoint pairs, timer expiry, retained current value and scale flag clearing. Full collision, draw and GPU equivalence are outside this helper proof.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletTh14.hpp','cpp/game/BulletState.hpp','cpp/game/Movement.cpp','cpp/game/Timer.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-size-native.py','tools/th14-bullet-size-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-size-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.initializations} ETEX 0x400000 setups / ${report.frames} motion frames.`);
