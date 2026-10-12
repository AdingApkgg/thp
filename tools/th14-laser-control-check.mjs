import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-control-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-laser-control-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'control.wasm'),fixture='tests/cpp/th14-laser-control-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-control-native.json'),'utf8')),p=c.allocate(38*4),a=c.allocate(12);let cases=0;
try{for(const [i,r] of proof.cases.entries())for(const local of [0,1]){
 new Uint32Array(c.memory.buffer,p,38).set(r.before.flat());new Uint32Array(c.memory.buffer,a,3).set(r.args);assert.equal(c.run(r.op,r.kind,p,a,local),0,`case ${i} local ${local}`);
 assert.deepEqual(Array.from({length:38},(_,j)=>c.value(j)>>>0),r.result.flat(),`case ${i} local ${local} state`);++cases;
}}finally{c.release(p);c.release(a);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-laser-control-verified.json'),JSON.stringify({passed:true,cases,nativeCases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'ECL 704..709 on kind 1/2/3 objects, id 0, present first/second and missing ids. Actual retail registry lookup and 705 velocity helper; only ECL argument reads are boundaries. Immediate/local routes in the production command. Compares position, angle, length, width, speed, id and first 11 request words. Kind 0 and downstream effects of mutated curve/shell request fields are outside.',sourceHashes:Object.fromEntries([fixture,'cpp/game/EnemyTh14Commands.cpp','cpp/game/LaserManager.cpp','cpp/game/LaserState.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-control-native.py','tools/th14-laser-control-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${cases} laser controls (${proof.cases.length} native x immediate/local).`);
