import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/item-ordinary-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-item-ordinary-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'item-ordinary.wasm'),fixture='tests/cpp/th16-item-ordinary-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/item-ordinary-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.run_case(r.kind,r.count,r.drop,...r.position,Number(r.full),r.angle,r.speed,r.force),0,JSON.stringify({index,...r}));
 assert.deepEqual(Array.from({length:24},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify({index,...r}));
 assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>c.event(n)>>>0),r.events,JSON.stringify({index,...r}));
}
c.reset();for(const slot of proof.allocations)assert.equal(c.spawn_next(),slot);
assert.equal(c.count()>>>0,proof.countAfter);c.recycle(proof.recycled.slot);assert.equal(c.spawn_next(),proof.recycled.slot);assert.equal(c.state(proof.recycled.slot),proof.recycled.state);assert.equal(c.free_slot(),proof.recycled.head);assert.equal(c.count()>>>0,proof.recycled.count);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-item-ordinary-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,allocations:proof.allocations.length,recycling:proof.recycled,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Complete own430960 ordinary factory1-8/15 and430d10 notice branches with40d460 binder,40e5c0 effect factory and45e150 sound delivery controlled. Real405610 free-list removal executes. Compare reverse-pool allocation, exhaustion, counter wrapping, type15 drop counter/6 conversion, clamp, velocity/timer, retained angle/generation, two script indexes112-119/134-141, white primary color and notice requests101 with sounds74/48. Portable binds synthetic stop ANMs. Full native ANM, production notice consumer, future item update/pickup and rendering excluded.',sourceHashes:Object.fromEntries(['cpp/game/ItemTh16.cpp','cpp/game/ItemManager.hpp','cpp/game/ItemManager.cpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');console.log(`PASS ${proof.cases.length} own TH16 ordinary item factories, ${proof.allocations.length} allocations and recycling`);
