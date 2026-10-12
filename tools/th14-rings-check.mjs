import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/rings-check');
mkdirSync(out,{recursive:true});
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-rings-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/rings-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmGeometry','AnmManager','AnmInterpreter','AnmResource','Interpolation'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-rings-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,p=c.allocate(120);assert.ok(p);
for(const row of proof.allocations){
 assert.equal(c.allocation_case(row.op,row.count,row.refs,row.initialMode),row.bytes,JSON.stringify(row));
 assert.equal(c.mode(),row.mode,JSON.stringify(row));
}
let vertexCount=0,wordDifferences=0,maxAbsoluteDifference=0;const firstWordDifferences=[];
const word=v=>new Uint32Array(new Float32Array([v]).buffer)[0];
for(const [index,row] of proof.cases.entries()){
 new Float32Array(c.memory.buffer,p,30).set([...row.position,...row.script,...row.child,...row.rotation,...row.scale,...row.variables,...row.uv,...row.uvOffset,...row.parentPosition,...row.parentRotation]);
 assert.equal(c.vertices_case(row.mode,row.count,row.flags,row.colorMode,row.displayScale,Number(row.parent),p,row.uvCycles,row.primary,row.secondary),0,`case ${index} mode ${row.mode}`);
 assert.equal(c.invalid_capacity(),0,'reject undersized output buffer');
 for(const [i,v] of row.vertices.entries()){
  const expected=[...v.position,...v.uv,...(v.rhw===null?[]:[v.rhw])];
  for(const [field,want] of expected.entries()){
   const actual=c.vertex(i,field),tolerance=Math.max(0.000004,Math.abs(want)*0.00000024);
   if(word(actual)!==word(want)){++wordDifferences;maxAbsoluteDifference=Math.max(maxAbsoluteDifference,Math.abs(actual-want));if(firstWordDifferences.length<16)firstWordDifferences.push({case:index,mode:row.mode,vertex:i,field,actual,expected:want,actualWord:word(actual),expectedWord:word(want)});}
   assert.ok(Math.abs(actual-want)<=tolerance,`case ${index} mode ${row.mode}, vertex ${i} field ${field}: ${actual} != ${want}`);
  }
  assert.equal(c.color(i)>>>0,v.color,`case ${index}, vertex ${i} color`);++vertexCount;
 }
}
c.release(p);
const report={passed:true,completeGame:false,nativeEquivalent:false,wordExact:wordDifferences===0,wordDifferences,maxAbsoluteDifference,firstWordDifferences,nativeExecutableSha256:proof.executableSha256,nativeAllocationCases:proof.allocations.length,nativeGeometryCases:proof.cases.length,vertices:vertexCount,
 scope:'TH14 ring allocation sizes/reference arguments and modes 9/13/14/23/24 vertex buffers through the production geometry manager. Positions/UV/RHW use tolerance max(0.000004,abs(expected)*0.00000024); color words exact. Separate float-word audit records every difference. Native allocator is a recorded boundary. Device rendering is not asserted.',wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmVm.hpp','cpp/game/AnmGeometry.hpp','cpp/game/AnmOpcodes.hpp','cpp/game/AnmManager.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-rings-native.py','tools/th14-rings-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-rings-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS tolerance: ${proof.allocations.length} native TH14 allocations; ${proof.cases.length} ring buffers / ${vertexCount} vertices; ${wordDifferences} float-word differences (maxAbs=${maxAbsoluteDifference}).`);
