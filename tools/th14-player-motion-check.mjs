import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/player-motion-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th14-player-motion-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-player-motion-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'motion.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/player-motion-native.json'),'utf8'));
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,held:r.held,env:r.env,transition:r.transition,variant:r.variant,previous:r.previous,rate:r.rate,count:r.count,active:r.active});assert.equal(c.begin(r.held,r.env,r.transition,r.variant,r.previous,r.rate,r.count,r.active),1,why);
 assert.deepEqual(Array.from({length:20},(_,n)=>c.value(n)>>>0),r.output,why);
 assert.deepEqual(Array.from({length:66},(_,n)=>c.history(n)>>>0),r.history,why);
 assert.deepEqual(Array.from({length:8},(_,n)=>Array.from({length:6},(_,k)=>c.option(n,k)>>>0)),r.options,why);
 assert.deepEqual(Array.from({length:17},(_,n)=>Array.from({length:7},(_,k)=>c.animation(n,k)>>>0)),r.animations,why);
 assert.equal(!!c.focus(),r.focus,why);assert.equal(c.body_script(),r.body,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-player-motion-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,completeGame:false,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Whole44d330 executes keyboard direction, focus gates and native184b0 focus/weapon field, SSE bomb displacement/rate, body script choice, clamps, 33-entry movement history and eight option slots. Cases exercise zero through eight active callback-free slots, snap/interpolation/recall retirement, full focus scale/position/flag delivery and root option VM positions. ANM lookup/bind/tick/interrupt controlled; focus allocation uses an existing valid handle, missing focus handle and nonzero option callbacks excluded. Synthetic animation resources, no native player lifecycle/campaign/GPU equivalence. Native recall bit2 is normalized to portable bit8.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp','cpp/game/PlayerFrame.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-player-motion-native.py','tools/th14-player-motion-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');console.log(`PASS ${proof.rows.length} full native TH14 movement/eight-option cases`);
