import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/spell-timing-check');mkdirSync(out,{recursive:true});
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-spell-timing-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-timing-native.json'),'utf8')),sources=['cpp/game/SpellTiming.cpp','tests/cpp/th14-spell-timing-fixture.cpp'],path=resolve(out,'timing.wasm');
assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const state=r=>[r.flags,r.frames,r.encoded,r.index,...r.startWords,...r.records];
for(const [n,r] of native.rows.entries()){assert.equal(c.begin(r.start,r.flags,r.frames,+r.replay,r.index,r.record),1);assert.deepEqual(Array.from({length:26},(_,k)=>c.word(k)>>>0),state(r.first),`sample${n} begin`);assert.equal(c.end(r.now,r.frames,+r.replay),1);assert.deepEqual(Array.from({length:26},(_,k)=>c.word(k)>>>0),state(r.last),`sample${n} end delta=${r.now-r.start}`);}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-spell-timing-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,scope:native.scope,wasmSha256:sha(bytes),nativeExecutableSha256:native.executableSha256,sourceHashes:Object.fromEntries([...sources,'cpp/game/SpellTiming.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-spell-timing-check.mjs','tools/th14-spell-timing-native.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS ${native.rows.length} original spell-clock begin/end states and20-entry records`);
