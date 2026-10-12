import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/bullet-draw-prep-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-bullet-draw-prep-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th16-bullet-draw-prep-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/bullet-draw-prep-native.json'),'utf8'));
const state=()=>Array.from({length:12},(_,n)=>c.word(n)>>>0);
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.rotate,r.scaled,r.angle,r.scale),0,`case ${i}`);assert.deepEqual(state(),r.words,`case ${i} state`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');const report={passed:true,title:16,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail primary bullet draw preparation block 412b62..412c02 compared with actual BulletManager::draw_group. Verifies entity XYZ copy and preserved script XYZ, rotation normalization/dirty flag, scale dirty flag, preserved ANM base scale and replacement of extra scale over 120 flag/angle/scale combinations. Native stops before GPU dispatch; WASM uses an invisible VM. This verifies preparation, not GPU pixels, culling or secondary ANM.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BulletTh14.cpp','cpp/game/BulletTh14.hpp','cpp/game/BulletState.hpp','cpp/game/Movement.cpp','cpp/game/BulletManager.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th16-bullet-draw-prep-native.py','tools/th16-bullet-draw-prep-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th16-bullet-draw-prep-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} TH16 bullet draw preparation cases.`);
