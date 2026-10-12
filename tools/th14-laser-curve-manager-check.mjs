import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-curve-manager-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-laser-curve-manager-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-laser-curve-rectangle-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'manager.wasm'),fixture='tests/cpp/th14-laser-curve-manager-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-manager-native.json'),'utf8')),p=c.allocate(120*32);let effects=0;
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,r.initial.length*8).set(r.initial.flat());assert.equal(c.run(p,r.initial.length,r.color,r.state,r.protection,r.mode),1,`case ${i}`);
 assert.deepEqual(Array.from({length:5},(_,j)=>c.value(j)>>>0),r.result,`case ${i} state`);
 assert.deepEqual(Array.from({length:c.effect_count()},(_,j)=>Array.from({length:6},(_,k)=>c.effect_word(j*6+k)>>>0)),r.effects,`case ${i} effects`);effects+=r.effects.length;
}}finally{c.release(p);}
const rectangles=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-rectangle-native.json'),'utf8')),points=c.allocate(256*32),req=c.allocate(0x354);let rectangleCases=0,fragmentFactories=0;
const asFloat=bits=>new Float32Array(new Uint32Array([bits]).buffer)[0];
for(const [i,r] of rectangles.cases.entries()){
 if(!r.skip)continue;new Uint32Array(c.memory.buffer,points,r.initial.length*8).set(r.initial.flat());new Uint32Array(c.memory.buffer,req,213).set(r.request);
 assert.equal(c.rectangle(points,r.initial.length,req,...r.center,...r.size,r.angle,r.rate,r.protection),r.count,`rectangle ${i}`);
 assert.deepEqual(Array.from({length:6},(_,j)=>c.value(j)>>>0),[r.flags&2,r.samples.length,...r.timer,1+r.fragments.length],`rectangle ${i} state/registry`);
 assert.deepEqual(Array.from({length:c.reward_count()},(_,j)=>Array.from({length:4},(_,k)=>c.reward_word(j*4+k)>>>0)),r.rewards,`rectangle ${i} rewards`);
 assert.deepEqual(Array.from({length:c.effect_count()},(_,j)=>Array.from({length:6},(_,k)=>c.effect_word(j*6+k)>>>0)),r.effects.map(e=>[...e,0x200,0]),`rectangle ${i} effects`);
 assert.equal(c.fragment_count(),r.fragments.length,`rectangle ${i} fragments`);
 for(const [j,f] of r.fragments.entries()){const expected=f.slice();expected[0x34c/4]=0;const t=Math.trunc(asFloat(f[0x350/4]));expected.push(99,(t-1)>>>0,t>>>0,f[0x350/4]);assert.deepEqual(Array.from({length:217},(_,k)=>c.fragment_word(j,k)>>>0),expected,`rectangle ${i} factory ${j}`);++fragmentFactories;}
 ++rectangleCases;
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-laser-curve-manager-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length,effects,rectangleCases,fragmentFactories,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 4436d0 full curve cancellation and 43aaf0 ECL 545 reset. Compares state, protection, offscreen clock and every-third-sample ANM script/position/flags requests. ANM pool allocation/binding/update/registration are boundaries; no native resource animation or pixels claim. Additionally integrates 442a00 request results through the production rotated-rectangle manager and real inherited-fragment factory under blank controlled ANM scripts; compares rewards/effects, parent clock/length/mark, registry count, all fragment request words, transform index and initial clock. Sample geometry and later fragment frames have independent proofs.',sourceHashes:Object.fromEntries([fixture,'cpp/game/LaserManager.cpp','cpp/game/LaserManager.hpp','cpp/game/LaserState.hpp','cpp/game/LaserCurveTh14Runtime.cpp','cpp/game/GameBattle.hpp','cpp/game/EnemyManager.cpp','cpp/game/LaserCurveTh14.cpp','cpp/game/LaserCurveTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-curve-manager-native.py','tools/th14-laser-curve-rectangle-native.py','tools/th14-laser-curve-manager-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} curve cancellations / resets, ${effects} ANM deliveries; ${rectangleCases} rectangle integrations / ${fragmentFactories} inherited factories.`);
