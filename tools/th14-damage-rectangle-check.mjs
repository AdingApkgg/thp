import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/damage-rectangle-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-damage-rectangle-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th14-damage-circle-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/damage-rectangle-native.json'),'utf8'));
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin_rectangle(r.cursor,r.occupied,r.duration,r.rate,r.variant),0,`allocation ${i}`);
 assert.equal(c.meta(0),r.index,`index ${i}`);assert.equal(c.meta(1),r.resultCursor,`cursor ${i}`);
 for(let j=0;j<r.frames.length;++j){if(j)c.tick();assert.deepEqual(Array.from({length:19},(_,n)=>c.word(n)>>>0),r.frames[j],`rectangle ${i} frame ${j}`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,allocations:proof.cases.length,updateFrames:proof.cases.length*64,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 450270 rectangular damage-area allocation and actual 44e005..44e0fa pool clock loop. Partial occupancy/wrap, retained unrelated fields, flag masking, width/height, zero angular velocity and angle normalization, stationary XYZ, timer and retirement; 240 cases with 64 updates each. Movement helpers 403cd0/403df0 and memset are controlled boundaries; only stationary movement is supported by this normalized model. Full-pool native out-of-range return remains guarded. This verifies rectangle allocation and stationary retirement, not the full Bomb controller or moving damage areas.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotDamageTh14.cpp','cpp/game/ShotDamageTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-damage-rectangle-native.py','tools/th14-damage-circle-native.py','tools/th14-damage-rectangle-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-damage-rectangle-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.allocations} rectangles / ${report.updateFrames} stationary update frames.`);
