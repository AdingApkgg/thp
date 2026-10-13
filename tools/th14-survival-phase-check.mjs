import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/survival-phase-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-survival-phase-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/EnemyPhase.cpp','tests/cpp/th14-enemy-phase-fixture.cpp'],wasm=resolve(out,'phase.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/survival-phase-native.json'),'utf8'));
for(const [n,row] of proof.rows.entries()){const p=c.allocate(row.inputs.length*4);try{new Uint32Array(c.memory.buffer,p,row.inputs.length).set(row.inputs);c.run(p);assert.deepEqual(Array.from({length:23},(_,i)=>c.value(i)>>>0),row.result,`phase ${n}`);}finally{c.release(p);}}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,completeGame:false,nativeEquivalent:false,productionChanged:false,nativeProofSha256:sha(readFileSync(resolve(root,'artifacts/th14/survival-phase-native.json'))),toolHashes:Object.fromEntries(['tools/th14-survival-phase-native.py','tools/th14-survival-phase-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))])),cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,scope:'Actual retail42bf70 on the observed health1/flag4093005c survival state: clocks1961,2699,2700,2701,7199,7200,7201 with timeout2700/7200, spell flags49/4b/9 and bomb active0/1. Native and production timer reset, countdown, interrupt, spell and bonus words exact. Unit boundary only; not Native complete phase execution or whole-game equivalence.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EnemyState.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-survival-phase-verified-oct13.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} native phase cases.`);
