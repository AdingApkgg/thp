import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/ecl-scalar-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-ecl-scalar-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/EclInterpreter.cpp','cpp/game/EclContext.cpp','cpp/game/EclOwner.cpp','cpp/game/EclResource.cpp','cpp/game/Interpolation.cpp','tests/cpp/th16-ecl-scalar-fixture.cpp'],wasm=resolve(out,'scalar.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',...sources,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/ecl-scalar-native.json'),'utf8'));let frames=0;
for(const [index,r] of proof.cases.entries()){
 const b=Buffer.from(r.code,'hex'),p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);c.begin(p,...r.input);
 try{for(const [frame,f] of r.timeline.entries()){
  assert.equal(c.tick()>>>0,f.result,`case${index}/${frame} result`);
  assert.deepEqual(Array.from({length:4},(_,n)=>c.value(n)>>>0),[f.time,f.offset,f.top,f.target],`case${index}/${frame} VM`);
  assert.deepEqual(Array.from({length:96},(_,n)=>c.slot_word(n)>>>0),f.slots,`case${index}/${frame} slots`);++frames;
 }}finally{c.release(p);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-ecl-scalar-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,timelines:proof.cases.length,frames,nativeExecutableSha256:proof.executableSha256,scope:'Full472030 VM91/92, eight original4171c0 scalar slots, modes0..31, negative/zero/positive durations, eight rates and two local frame bases. Original argument resolvers, replacement of an active slot, end-of-frame destination re-resolution and wait-path consumers execute. Extended opcode99 is a controlled wait boundary. Calls/threads, negative global destinations, GPU and complete game excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EclRoutes.hpp','cpp/game/EclContext.hpp','cpp/game/EclOwner.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 ECL scalar timelines / ${frames} frames, exact fields`);
