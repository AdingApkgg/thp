import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-heading-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-heading-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'bullet-heading.wasm'),fixture='tests/cpp/th14-bullet-heading-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-heading-native.json'),'utf8'));
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.index,r.active,r.concurrent,r.angle,r.speed),0,`case ${i} canonical result`);
 assert.deepEqual(Array.from({length:8},(_,j)=>c.word(j)>>>0),r.state,`case ${i} state`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');const sources=[fixture,'cpp/game/BulletTh14.cpp','cpp/game/Movement.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Complete retail 418140 ETEX 40000 dispatch with actual player-aim, normalization and polar helper instructions. Compares active mask/index, scalar speed/angle and all velocity components, and non-concurrent gate with active ETEX 4. Finite explicit/aim/preserve sentinels and bounded angle normalization included. EAX is an unspecified dispatcher residue and is not interpreted as a result. Motion/update, collision, ANM, sound and pixels are outside this local check.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-heading-native.py','tools/th14-bullet-heading-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-heading-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} original ETEX 40000 dispatcher cases.`);
