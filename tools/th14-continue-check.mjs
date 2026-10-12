import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/continue-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-continue-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-continue-fixture.cpp',wasm=resolve(out,'continue.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,'cpp/game/ContinueTh14.cpp','-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/continue-native.json'),'utf8'));
for(const row of proof.rows){assert.equal(c.run(row.maximum,row.step,row.continues,row.bombFragments),Number(row.capped),JSON.stringify(row));assert.deepEqual(Array.from({length:7},(_,i)=>c.value(i)),row.result,JSON.stringify(row));assert.deepEqual(Array.from({length:5},(_,i)=>c.value(i+7)),[3456,789,-512,17,2]);assert.equal(row.remaining,4);assert.equal(row.controlFlags,0x3507);if(row.capped)assert.deepEqual(row.notice,[[0,2]]);}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 44ae10..44aee9 and original 447a80: restored life/bomb stocks and fragments, power and clamp notice condition, score reset and capped Continue count. HUD/option refresh boundaries; excludes native respawn, audio, extra-stage transition and pixel output. Port-only preservation assertions for PIV/graze/rank/item/extend counters.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ContinueTh14.cpp','cpp/game/ContinueTh14.hpp','cpp/game/GameEconomy.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-continue-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} native Continue counter cases.`);
