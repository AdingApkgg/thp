import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/item-drop-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-item-drop-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-item-drop-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'drop.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/item-drop-native.json'),'utf8')),f32=new Float32Array(1),u32=new Uint32Array(f32.buffer),toFloat=b=>{u32[0]=b;return f32[0]},toBits=f=>{f32[0]=f;return u32[0]};
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.begin(r.seed,r.flags,r.primary,index%8,...r.position,...r.spread),0,JSON.stringify(r));
 assert.deepEqual(Array.from({length:16},(_,n)=>c.value(n)>>>0),r.result,JSON.stringify(r));
 assert.equal(c.spawn_count(),r.requests.length);
 for(const [n,a] of r.requests.entries()){
  const x=Math.min(192,Math.max(-192,toFloat(a[1]))),angle=toFloat(a[4]),speed=toFloat(a[5]);
  assert.deepEqual(Array.from({length:7},(_,k)=>c.spawn_value(n,k)>>>0),[a[0],toBits(x),a[2],a[3],toBits(Math.cos(angle)*speed),toBits(Math.sin(angle)*speed),a[6]],JSON.stringify({r,n}));
 }
}
assert.deepEqual([c.other_rng(0),c.other_rng(1)],[54321,123],'ANM/shake RNG remains untouched');
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/ItemManager.hpp','cpp/game/ItemManager.cpp','cpp/game/ItemTh14.cpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyManager.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Both native and production item paths consume the 4db510 stream (animations.visual_rng) and preserve a seeded 4db508 ANM/shake stream. Retail ECL 509 4277fd -> 421560/4215b0 against production EnemyScriptServices dispatch and ItemManager::drop. Spell-practice mask 0x30==0x20 skips all side effects. Ordinary power/point types 1/2: initial signed RNG even for empty drops, per-item unit/random turns, polar scatter, wrapping angle, allocation order and clamped positions. Native loop emits types 1..12 but clears thirteen count words; the thirteenth nonzero word is tested. Native 4397b0 factory is controlled here; its actual type-1/2 pool allocation, timers and two ANM requests are measured separately in th14-item-verified.json. The port uses synthetic ANM scripts. Other item types, ordinary pickup/auto-attract combo rewards, resource animation pixels and complete gameplay remain unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};writeFileSync(resolve(root,'docs/porting/th14-item-drop-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} ECL 509/native scatter cases.`);
