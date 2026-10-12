import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/graze-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-graze-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const wasm=resolve(out,'graze.wasm'),sources=['tests/cpp/th14-graze-fixture.cpp','cpp/game/GameEconomy.cpp'];
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,p=c.allocate(36);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/graze-native.json'),'utf8'));
try{for(const [i,r] of proof.cases.entries()){new Uint32Array(c.memory.buffer,p,9).set(r.input);c.run(p);assert.deepEqual(Array.from({length:7},(_,j)=>c.value(j)>>>0),r.result,`case ${i}`);}}finally{c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-graze-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 450410 graze counter saturation, signed wrapped point-value addition/clamp, effect-24 midpoint and sound-42/contact-X. ANM/audio delivery are boundaries. No claim for all collision producers, effect animation or sound waveform.',sourceHashes:Object.fromEntries([...sources,'cpp/game/GameEconomy.hpp','cpp/game/GameBattle.cpp','cpp/game/LaserCurveTh14Runtime.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-graze-native.py','tools/th14-graze-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} native TH14 graze cases.`);
