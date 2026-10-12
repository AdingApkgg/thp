import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/ecl-vm-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-ecl-vm-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/EclInterpreter.cpp','cpp/game/EclContext.cpp','cpp/game/EclOwner.cpp','cpp/game/EclResource.cpp','cpp/game/Interpolation.cpp','tests/cpp/th16-ecl-vm-fixture.cpp'],wasm=resolve(out,'vm.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',...sources,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/ecl-vm-native.json'),'utf8'));
for(const [index,row] of proof.cases.entries()){
 const b=Buffer.from(row.code,'hex'),p=c.allocate(b.length),data=c.allocate(768);new Uint8Array(c.memory.buffer,p,b.length).set(b);new Uint32Array(c.memory.buffer,data,192).set(row.initial);
 try{assert.equal(c.run_case(p,data,row.time,row.rate,row.seed)>>>0,row.output.result,`case ${index} op ${row.opcode}`);
  assert.deepEqual([0,1,2].map(k=>c.value(k)>>>0),[row.output.time,row.output.offset,row.output.top],`case ${index} op ${row.opcode} state`);
  assert.deepEqual([c.rng_value(0),c.rng_value(1)],row.rng,`case ${index} RNG`);
  // The popped dead cells need not retain the CPU's temporary writes.
  const slots=new Set([...Array.from({length:row.output.top/4},(_,i)=>i),128,129,130,131]);
  for(const slot of slots)assert.equal(c.value(slot+3)>>>0,row.output.stack[slot],`case ${index} op ${row.opcode} stack ${slot}`);
 }finally{c.release(p);c.release(data);}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,title:16,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,scope:'Full retail472030 VM on finite synthetic no-op/wait/stack/arithmetic/comparison/vector streams, actual native instruction-offset resolution and argument cleanup. Eight VM interpolator durations are zero. No calls, threads, global variable table, random polar, active interpolation, gameplay or GPU equivalence',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EclRoutes.hpp','cpp/game/Rng.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th16-ecl-vm-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} TH16 VM cases.`);
