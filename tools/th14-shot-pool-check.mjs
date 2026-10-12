import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-pool-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-shot-pool-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-shot-pool-fixture.cpp',wasm=resolve(out,'pool.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-pool-native.json'),'utf8'));
const state=()=>{const free=[];for(let n=c.head();n<256;n=c.next_slot(n)){assert.ok(!free.includes(n));free.push(n);}return {free,active:Array.from({length:256},(_,i)=>i).filter(i=>c.is_active(i))};};
assert.deepEqual(state(),proof.initial);
let allocations=0,updates=0;
for(const [i,r] of proof.rows.entries()){
 c.run(r.args[0],r.args[1],r.args[2]??0);
 const events=Array.from({length:c.event_count()},(_,n)=>c.event_at(n));
 assert.deepEqual(events,r.args[0]?r.updates:r.attempts,`operation ${i} order`);
 assert.deepEqual(state(),{free:r.free,active:r.active},`operation ${i} pool`);
 allocations+=r.attempts.length;updates+=r.updates.length;
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-shot-pool-verified.json'),JSON.stringify({passed:true,operations:proof.rows.length,allocationAttempts:allocations,updates,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 44cdb7 initialization, 450e40 factory unlink and 451380 ascending-slot traversal/recycling. Covers exhaustion, failed factory requests, alternating and complete retirement, and reuse over repeated cycles. 4508f0 and 4510b0 are controlled result boundaries; ANM, individual shot lifecycle, damage-area order and full gameplay require separate checks.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotPoolTh14.hpp','cpp/game/ShotManager.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} retail pool operations / ${allocations} allocation attempts / ${updates} slot updates.`);
