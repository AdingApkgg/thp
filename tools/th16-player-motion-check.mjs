import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/player-motion-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-player-motion-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-player-motion-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/player-motion-native.json'),'utf8'));
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,held:r.held,env:r.env,transition:r.transition,seed:r.seed,previous:r.previous,rate:r.rate,charge:r.charge});assert.equal(c.begin(r.held,r.env,r.transition,r.seed,r.previous,r.rate,r.charge),1,why);
 assert.deepEqual(Array.from({length:24},(_,k)=>c.value(k)>>>0),r.output,why);
 assert.deepEqual(Array.from({length:2},(_,k)=>!!c.handle(k)),r.handles,why);
 assert.deepEqual(Array.from({length:c.animation_count()},(_,n)=>Array.from({length:7},(_,k)=>c.animation(n,k)>>>0)),r.animations,why);
 assert.deepEqual(Array.from({length:c.effect_count()},(_,n)=>c.effect(n)),r.events.filter(e=>e[0]===1).map(e=>e[1]),why);
 assert.equal(c.body_script(),r.events.filter(e=>e[0]===0).at(-1)?.[1]??0,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-player-motion-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,resources:proof.resources,wasmSha256:sha(bytes),scope:'Complete441cf0 on keyboard movement, missing/enabled enemy manager, startup focus suppression, fixed-point wrapping, SSE rate/displacement/factor, clamps, body script changes, focus scale/cache/missing handles, recall clock/count reset and full charge effect countdown. ANM binder/tick/create/lookup/family interrupt delivery controlled. All option states inactive here; active442380 is separately proven. Touch, resources/draw, player lifecycle and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp','cpp/game/ShtResource.cpp','cpp/game/AnmManager.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-player-motion-native.py','tools/th16-player-motion-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 player movement cases.`);
