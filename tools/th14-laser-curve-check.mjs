import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-curve-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-laser-curve-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-laser-curve-path-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-laser-curve-cut-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const wasm=resolve(out,'curve.wasm'),fixture='tests/cpp/th14-laser-curve-fixture.cpp';
const sources=[fixture,'cpp/game/LaserCurveTh14.cpp','cpp/game/Movement.cpp'];
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-native.json'),'utf8'));
const n=c.allocate(60),p=c.allocate(20);let compared=0;
try{for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,n,15).set(r.node);new Uint32Array(c.memory.buffer,p,5).set(r.previous);
 assert.equal(c.run(n,r.time,p,r.tail),r.valid,`case ${i} validity`);
 const actual=Array.from({length:5},(_,j)=>c.value(j)>>>0);
 assert.deepEqual(actual,r.result,`case ${i}: ${JSON.stringify(r)}`);compared+=5;
}}finally{c.release(n);c.release(p);}
const paths=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-path-native.json'),'utf8'));
const req=c.allocate(0x354);let sampledWords=0,meshWords=0;
const compareNodes=(expected,label)=>{
 assert.equal(c.node_count(),expected.length,label);
 for(const [i,n] of expected.entries())assert.deepEqual(Array.from({length:15},(_,j)=>c.node_word(i,j)>>>0),n,`${label} node ${i}`);
};
const compareSamples=(expected,label)=>{
 for(const [i,s] of expected.entries()){assert.deepEqual(Array.from({length:8},(_,j)=>c.sample_word(i,j)>>>0),s,`${label} sample ${i}`);sampledWords+=8;}
};
try{for(const [i,r] of paths.cases.entries()){
 new Uint32Array(c.memory.buffer,req,213).set(r.request);assert.equal(c.initialize(req),1,`path ${i} initialize`);
 compareNodes(r.initialNodes,`path ${i} initial`);compareSamples(r.initial,`path ${i} initial`);
 assert.equal(c.transforms(),1,`path ${i} transforms`);compareNodes(r.nodes,`path ${i} ETEX`);
 for(const [j,f] of r.frames.entries()){
  c.sample(f.time);compareSamples(f.samples,`path ${i} frame ${j}`);c.mesh();
  for(const [k,v] of f.mesh.entries()){assert.deepEqual(Array.from({length:7},(_,n)=>c.mesh_word(k,n)>>>0),v,`path ${i} frame ${j} vertex ${k}`);meshWords+=7;}
 }
}}finally{c.release(req);}
const cuts=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-cut-native.json'),'utf8'));
const points=c.allocate(256*32);
try{for(const [i,r] of cuts.cases.entries()){
 new Uint32Array(c.memory.buffer,points,r.initial.length*8).set(r.initial.flat());c.load_samples(points,r.initial.length);
 assert.equal(c.cut_circle(...r.center,r.radius,r.protection,r.skip),r.count,`cut ${i} count`);
 assert.equal(c.marked(),r.flags===2?1:0,`cut ${i} mark`);assert.equal(c.sample_count(),r.samples.length,`cut ${i} length`);
 compareSamples(r.samples,`cut ${i}`);
 const deliveries=Array.from({length:c.delivery_count()},(_,j)=>Array.from({length:3},(_,k)=>c.delivery_word(j,k)>>>0));
 assert.deepEqual(deliveries,r.rewards.map(v=>v.slice(1)),`cut ${i} rewards`);assert.deepEqual(deliveries,r.effects.map(v=>v.slice(1)),`cut ${i} effects`);
 assert.ok(r.rewards.every(v=>v[0]===1));assert.ok(r.effects.every(v=>v[0]===209));
}}finally{c.release(points);}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,cases:proof.cases.length,comparedWords:compared,pathCases:paths.cases.length,circleCuts:cuts.cases.length,sampledWords,meshWords,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 440f60 / 441430 analytic modes 0/1/2; actual x87 polar, floor, sqrt and atan2 without substituted helpers. Retail 4401d0 initialization with zero inherited-node pointer, 441e40 ETEX 4/8, 440a7d sampling and 4418e0 mesh generation include the first stage-four ECL 711 request. Retail 4433d0 circle selection, prefix removal, tail truncation and full-selection marking compare reward/effect requests. ANM reset/bind/tick, allocation, sound and reward/effect delivery are controlled boundaries. No claim for other ETEX, ANM resources, segment collision, graze delivery, rectangle cutting, GPU submission or complete ECL 711.',sourceHashes:Object.fromEntries([...sources,'cpp/game/LaserCurveTh14.hpp','cpp/game/Movement.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-curve-native.py','tools/th14-laser-curve-path-native.py','tools/th14-laser-curve-cut-native.py','tools/th14-laser-curve-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-laser-curve-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} analytic cases / ${compared} raw float32 words; ${report.pathCases} paths, ${sampledWords} sample words and ${meshWords} mesh words.`);
