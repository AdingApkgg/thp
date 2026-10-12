import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/option-motion-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-option-motion-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-option-motion-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/option-motion-native.json'),'utf8'));
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,...r});assert.equal(c.begin(r.base,r.focus,r.recall,r.clock,r.lerp,r.seed,r.snap,r.present),1,why);
 assert.deepEqual(Array.from({length:12},(_,i)=>Array.from({length:11},(_,k)=>c.option(i,k)>>>0)),r.options,why);
 assert.deepEqual(Array.from({length:24},(_,n)=>Array.from({length:4},(_,k)=>c.animation(n,k)>>>0)),r.animations,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-option-motion-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,resources:proof.resources,wasmSha256:sha(bytes),scope:'Complete442380: both main/season arrays, focused targets, flags2 recall,30-frame exit, integer wrapping and signed division interpolation, snap, missing handles and exact SSE coordinates. Per-option callbacks zero; VM lookup and family interrupts controlled. Actual child callback delivery, animation resources, body movement and complete player lifecycle excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp','cpp/game/ShtResource.cpp','cpp/game/AnmManager.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-option-motion-native.py','tools/th16-option-motion-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 option movement cases.`);
