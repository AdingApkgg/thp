import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-flags-check');mkdirSync(out,{recursive:true});
execFileSync('py',['-3','tools/th14-enemy-flags-native.py'],{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/EnemyTh14Commands.cpp','tests/cpp/th14-enemy-flags-fixture.cpp'],wasm=resolve(out,'flags.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-flags-native.json'),'utf8'));
for(const row of proof.cases){const label=JSON.stringify(row);assert.equal(c.run_case(row.opcode,row.flags,row.bits,row.pattern),0,label);assert.equal(c.flags()>>>0,row.result,label);assert.deepEqual(Array.from({length:c.count()*2},(_,i)=>c.call_value(i)),row.calls.flat(),label);}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,
 scope:'Retail 502/503 flag word and nonzero animation-handle visibility calls, including all sixteen slots. Argument resolution and native ANM lookup are boundaries; the full enemy runtime remains unverified.',wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/EnemyState.hpp','cpp/game/EnemyScript.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-enemy-flags-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} TH14 enemy flag/visibility cases.`);
