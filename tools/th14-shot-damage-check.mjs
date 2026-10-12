import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-damage-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-shot-damage-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th14-shot-damage-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-damage-native.json'),'utf8')),p=c.allocate(68*4);
try{for(const [i,r] of proof.rows.entries()){
 new Uint32Array(c.memory.buffer,p,68).set(r.input);assert.equal(c.run(p),1,`collector ${i}`);const expected=[...r.result];expected[1]=expected[1]?1:0;
 assert.deepEqual(Array.from({length:22},(_,j)=>c.value(j)>>>0),expected,`collector ${i} state`);
}}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-shot-damage-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,circularAreaCases:6144,rectangularAreaCases:proof.rows.length-6144,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 451430 collector with circular and rectangular damage areas, actual 404ca0 circle/rotated rectangle and 4061f0 rotated rectangle helpers and native math. Three occupied slots in a 256-slot pool; frame/period/probe/stamp gates, callback returns/order, accumulated damage, cap/score, area retirement and last-hit position. Bomb class inactive; callbacks supplied and recorded. Native pool allocation/movement, shot ownership and production callback effects are outside this proof. Production integrates attached-shot areas; Bomb/death areas and complete shot lifecycle remain unfinished.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotDamageTh14.cpp','cpp/game/ShotDamageTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-shot-damage-native.py','tools/th14-shot-damage-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.rows.length} damage collector cases.`);
