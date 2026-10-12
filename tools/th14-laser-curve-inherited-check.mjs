import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-curve-inherited-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-laser-curve-inherited-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-laser-curve-fixture.cpp','cpp/game/LaserCurveTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'curve.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-curve-inherited-native.json'),'utf8')),req=c.allocate(0x354),nodes=c.allocate(37*60);let frames=0,words=0;
const compare=(samples,label)=>{assert.equal(c.sample_count(),samples.length,label);for(const [i,s] of samples.entries()){assert.deepEqual(Array.from({length:8},(_,j)=>c.sample_word(i,j)>>>0),s,`${label} ${i}`);words+=8;}};
for(const [i,r] of proof.cases.entries()){
 new Uint32Array(c.memory.buffer,req,213).set(r.request);new Uint32Array(c.memory.buffer,nodes,r.inheritedNodes.length*15).set(r.inheritedNodes.flat());assert.equal(c.initialize_inherited(req,nodes,r.inheritedNodes.length),1,`path ${i}`);assert.equal(c.transform_index(),99);assert.deepEqual(Array.from({length:213},(_,j)=>c.request_word(j)>>>0),r.copied,`path ${i} copied`);compare(r.initial,`path ${i} initial`);
 assert.equal(c.transforms(),1);assert.equal(c.node_count(),r.nodes.length);assert.deepEqual(Array.from({length:c.node_count()},(_,j)=>Array.from({length:15},(_,k)=>c.node_word(j,k)>>>0)),r.nodes,`path ${i} nodes`);
 for(const [j,f] of r.frames.entries()){c.sample(f.time);compare(f.samples,`path ${i} frame ${j}`);c.mesh();assert.deepEqual(Array.from({length:f.mesh.length},(_,k)=>Array.from({length:7},(_,n)=>c.mesh_word(k,n)>>>0)),f.mesh,`path ${i} frame ${j} mesh`);++frames;}
}
const sha=b=>createHash('sha256').update(b).digest('hex');const report={passed:true,paths:proof.cases.length,frames,sampleWords:words,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 4401d0 nonzero inherited-node branch copies complete analytic-node chains, clears request pointer and sets transform index 99; production clones compare initial sampling, 18 later times and mesh for 13 retail/synthetic ETEX 4/8 paths. Native ANM, allocation and sound are controlled. Does not prove registry links, clipping deliveries, collisions or GPU pixels.',sourceHashes:Object.fromEntries([...sources,'cpp/game/LaserCurveTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-curve-inherited-native.py','tools/th14-laser-curve-path-native.py','tools/th14-laser-curve-inherited-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};writeFileSync(resolve(root,'docs/porting/th14-laser-curve-inherited-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.paths} inherited paths / ${frames} sampled and meshed frames.`);
