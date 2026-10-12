import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/item-factory-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-item-factory-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'item-factory.wasm'),fixture='tests/cpp/th16-item-factory-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/item-factory-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.run_case(r.kind,r.count,r.load,Number(r.full),...r.position,r.angle,r.speed,r.force),0);
 assert.deepEqual(Array.from({length:20},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify({index,...r}));
}
c.reset();for(const slot of proof.allocations)assert.equal(c.spawn_next(),slot);
assert.equal(c.count()>>>0,proof.countAfter);c.recycle(proof.recycled.slot);assert.equal(c.spawn_next(),proof.recycled.slot);assert.equal(c.state(proof.recycled.slot),proof.recycled.state);assert.equal(c.free_slot(),proof.recycled.head);assert.equal(c.count()>>>0,proof.recycled.count);
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const r of proof.activation){assert.equal(c.activate(r.kind,r.season,r.flags),1,JSON.stringify(r));assert.deepEqual(Array.from({length:5},(_,n)=>c.activation_word(n)>>>0),r.output,JSON.stringify(r));}
writeFileSync(resolve(root,'docs/porting/th16-item-factory-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,poolLinks:proof.chains.map(c=>c.length),allocations:proof.allocations.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own430960 special factory types9-14 and16: reversed special free-list, exhaustion, signed counter wrapping and load thresholds, raw position, x87 polar velocity, timer initialization, generation, force attraction and430d90 recycling. Own4184a0 ordinary chain measured but ordinary allocation, full item lifecycle, pickup and rendering remain excluded.',sourceHashes:Object.fromEntries(['cpp/game/ItemTh16.cpp','cpp/game/ItemManager.hpp','cpp/game/ItemManager.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 special item factories, ${proof.allocations.length} allocations and free-list recycling`);
const reportPath=resolve(root,'docs/porting/th16-item-factory-verified.json'),report=JSON.parse(readFileSync(reportPath,'utf8'));report.activations=proof.activation.length;report.scope+=' Complete430c90 activation dispatch with binder and ANM tick boundaries, both state2/state3 and selected season129-132, parent clearing and indicator disable. Portable fixture binds actual synthetic stop scripts; real VM construction/rendering remains excluded.';writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(`PASS ${proof.activation.length} own TH16 delayed item activations`);
