import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-curve-rectangle-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-laser-curve-rectangle-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-laser-curve-fixture.cpp','cpp/game/LaserCurveTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'curve.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-rectangle-native.json'),'utf8')),p=c.allocate(256*32),req=c.allocate(0x354);let spawned=0;
for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,p,r.initial.length*8).set(r.initial.flat());c.load_samples(p,r.initial.length);new Uint32Array(c.memory.buffer,req,213).set(r.request);c.rectangle_request(req);
 assert.equal(c.cut_rectangle(...r.center,...r.size,r.angle,r.rate,r.protection,r.skip),r.count,`cut ${i} count`);assert.equal(c.marked(),+(r.flags===2),`cut ${i} mark`);assert.deepEqual([0,1,2].map(n=>c.rectangle_timer(n)>>>0),r.timer,`cut ${i} timer`);assert.equal(c.sample_count(),r.samples.length,`cut ${i} length`);
 assert.deepEqual(Array.from({length:c.sample_count()},(_,j)=>Array.from({length:8},(_,k)=>c.sample_word(j,k)>>>0)),r.samples,`cut ${i} samples`);
 const deliveries=Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:3},(_,k)=>c.delivery_word(j,k)>>>0));assert.deepEqual(deliveries,r.rewards.map(v=>v.slice(1)),`cut ${i} rewards`);assert.deepEqual(deliveries,r.effects.map(v=>v.slice(1)),`cut ${i} effects`);assert.ok(r.effects.every(e=>e[0]===209));
 assert.deepEqual(Array.from({length:c.fragment_count()},(_,j)=>Array.from({length:213},(_,k)=>c.fragment_word(j,k)>>>0)),r.fragments,`cut ${i} fragments`);spawned+=r.fragments.length;
}
const sha=b=>createHash('sha256').update(b).digest('hex');const report={passed:true,cases:proof.cases.length,fragmentRequests:spawned,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 442a00 rotated rectangle sample selection, protection, reward/effect requests, prefix timer advance with rates .5/1/1.25, native minimum surviving length, length retention and inherited-curve fragment requests. Native allocation, ANM lookup/effects and fragment construction are controlled; inherited pointer normalized to presence marker. Does not prove fragment factory execution, manager delivery, collision or GPU pixels.',sourceHashes:Object.fromEntries([...sources,'cpp/game/LaserCurveTh14.hpp','cpp/game/Timer.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-curve-rectangle-native.py','tools/th14-laser-curve-rectangle-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};writeFileSync(resolve(root,'docs/porting/th14-laser-curve-rectangle-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} rectangle cuts / ${spawned} fragment requests.`);
