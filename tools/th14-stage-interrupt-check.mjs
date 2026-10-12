import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/stage-interrupt-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-stage-interrupt-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'stage.wasm'),fixture='tests/cpp/th14-stage-interrupt-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/stage-interrupt-native.json'),'utf8'));
for(const r of proof.cases)for(const ecl of [0,1]){assert.equal(c.run(r.variant,r.marker,r.flags,r.pointer,ecl),0);assert.deepEqual(Array.from({length:6},(_,n)=>c.word(n)>>>0),r.result,JSON.stringify({...r,ecl}));}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-stage-interrupt-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length*2,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 410470 STD marker search, first matching opcode 16 before the negative-time sentinel, unchanged state when absent, next-instruction offset and timer/rate/flag updates. Direct stage interrupt and production ECL 630 routing both compared. Synthetic instruction streams; subsequent background execution, native ECL argument resolution and pixels are not asserted.',sourceHashes:Object.fromEntries([fixture,'cpp/game/StageScript.cpp','cpp/game/Timer.hpp','cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyScript.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-stage-interrupt-native.py','tools/th14-stage-interrupt-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length*2} STD / ECL 630 cases.`);
