import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/render-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-render-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/render-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','AnmProjection','AnmRenderer','GraphicsMath','Interpolation','SceneCamera'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-render-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
let vertices=0;
for(const [index,row] of proof.quads.entries()){
 assert.equal(c.quad_case(row.mode,row.colorMode,row.relation,row.tinted,row.visibility,row.sample)>>>0,row.status,`quad ${index} status`);
 assert.equal(c.draw_count(),row.draws.length,`quad ${index} submissions`);assert.equal(c.cached_color()>>>0,row.cachedColor,`quad ${index} inherited cache`);
 for(const quad of row.draws)for(const [i,vertex] of quad.entries()){
  for(const [f,want] of vertex.entries())if(f===4)assert.equal(c.vertex_color(i)>>>0,want,`quad ${index} vertex ${i} color`);
  else assert.ok(Math.abs(c.vertex_value(i,f)-want)<=Math.max(.00001,Math.abs(want)*.00000024),`quad ${index} vertex ${i} field ${f}: ${c.vertex_value(i,f)} != ${want}`);
  ++vertices;
 }
 const depth=row.events.find(e=>e[0]==='state'&&e[1]===14);if(depth)assert.equal(c.state_value(7),depth[2],`quad ${index} depth`);
}
for(const [index,row] of proof.materials.entries())for(let previous=0;previous<3;++previous){
 assert.equal(c.material_case(row.blend,row.u,row.v,row.point,previous),0);
 const expected=[9,7,2,2,2,[1,2,3][previous],[3,1,2][previous]];
 for(const [kind,key,value] of row.events){const i=kind==='state'?({19:0,20:1,171:2})[key]:({5:3,6:4,1:5,2:6})[key];assert.notEqual(i,undefined);expected[i]=value;}
 assert.deepEqual(expected.map((_,i)=>c.state_value(i)),expected,`material ${index} previous ${previous}`);
}
let stripVertices=0;
for(const [index,row] of proof.strips.entries()){
 assert.equal(c.strip_case(row.mode,row.parent,row.origin,row.depth,row.priorDepth,row.rotation),0,`strip ${index} return`);assert.equal(c.draw_count(),row.draws.length);
 assert.equal(row.draws.length,1);const d=row.draws[0];
 assert.deepEqual([0,1,2,3,4,5].map(i=>c.strip_metadata(i)),[d.count,d.stride,d.depth,d.fog,row.finalDepth,row.finalFog],`strip ${index} pipeline ${JSON.stringify(row)}`);
 assert.equal(c.strip_metadata(6)+1,d.topology);
 for(const [kind,matrix] of Object.entries(d.matrices))for(const [i,want] of matrix.entries()){
  const actual=c.strip_matrix(Number(kind)===16?1:0,i);assert.ok(Math.abs(actual-want)<=Math.max(.000001,Math.abs(want)*.0000003),`strip ${index} matrix ${kind}/${i}: ${actual} != ${want}`);
 }
 for(const [i,vertex] of d.vertices.entries())for(const [f,want] of vertex.entries()){
  if(f===(d.stride===24?3:4))assert.equal(c.strip_color(i)>>>0,want,`strip ${index} vertex ${i} color`);
  else assert.ok(Math.abs(c.strip_component(i,f)-want)<=Math.max(.000001,Math.abs(want)*.0000003),`strip ${index} vertex ${i}/${f}`);
 }
 stripVertices+=d.vertices.length;
}
let shapeVertices=0;
for(const [index,row] of proof.shapes.entries()){
 assert.equal(c.shape_case(row.mode,row.anchor,row.parent,row.resolution),0);assert.equal(c.draw_count(),row.draws.length,`shape ${index} draw count`);
 for(const [j,d] of row.draws.entries()){
  assert.deepEqual([0,1,2].map(f=>c.shape_metadata(j,f)),[d.count,d.stride,d.depth],`shape ${index} pipeline`);
  assert.equal(c.shape_metadata(j,3)+1,d.topology);
  for(const [i,vertex] of d.vertices.entries())for(const [f,want] of vertex.entries()){
   if(f===4)assert.equal(c.shape_color(j,i)>>>0,want,`shape ${index}/${j} vertex ${i} color`);
   else {const actual=c.shape_component(j,i,f);assert.ok(Math.abs(actual-want)<=Math.max(.00001,Math.abs(want)*.0000003),`shape ${index}/${j} vertex ${i}/${f}: ${actual} != ${want}`);}
  }
  shapeVertices+=d.vertices.length;
 }
}
for(const [index,row] of proof.worldQuads.entries()){
 assert.equal(c.world_case(row.parent,row.origin,row.resolution,row.order,row.anchor,row.depth,row.colorMode,row.tinted),0);assert.equal(c.draw_count(),row.draws.length);assert.equal(row.draws.length,1);const d=row.draws[0];
 assert.deepEqual([c.strip_metadata(0),c.strip_metadata(2),c.strip_metadata(6)+1,c.world_factor()>>>0],[d.count,d.depth,d.topology,d.factor],`world ${index} pipeline`);
 for(const [kind,matrix] of Object.entries(d.matrices))for(const [i,want] of matrix.entries()){
  const actual=c.strip_matrix(Number(kind)===16?1:0,i);assert.ok(Math.abs(actual-want)<=Math.max(.00001,Math.abs(want)*.0000003),`world ${index} matrix ${kind}/${i}: ${actual} != ${want}`);
 }
 for(const [i,vertex] of d.vertices.entries())for(const [f,want] of vertex.entries())assert.equal(c.strip_component(i,f),want,`world ${index} anchor ${i}/${f}`);
}
let screenStripVertices=0;
for(const [index,row] of proof.screenStrips.entries()){
 assert.equal(c.screen_strip_case(row.blend,row.visibility,row.count,row.priorDepth)>>>0,row.status,`screen strip ${index} status`);
 assert.equal(c.draw_count(),row.draws.length,`screen strip ${index} submissions`);
 if(!row.draws.length)continue;
 const d=row.draws[0];assert.deepEqual([c.strip_metadata(0),c.strip_metadata(1),c.strip_metadata(2),c.strip_metadata(6)+1],[d.count,d.stride,d.depth,d.topology]);
 for(const [i,vertex] of d.vertices.entries())for(const [f,want] of vertex.entries()){
  if(f===4)assert.equal(c.strip_color(i)>>>0,want);else assert.equal(c.strip_component(i,f),want,`screen strip ${index} ${i}/${f}`);
 }
 const expected=[9,7,2];for(const [kind,key,value] of row.events)if(kind==='state'&&[19,20,171].includes(key))expected[({19:0,20:1,171:2})[key]]=value;
 assert.deepEqual(expected.map((_,i)=>c.state_value(i)),expected,`screen strip ${index} material`);
 screenStripVertices+=d.vertices.length;
}
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativeD3dxSha256:proof.d3dxSha256,nativeQuadCases:proof.quads.length,submittedVertices:vertices,nativeMaterialCases:proof.materials.length,materialStateChecks:proof.materials.length*3,nativeStripCases:proof.strips.length,stripVertices,nativeShapeCases:proof.shapes.length,shapeVertices,nativeWorldQuadCases:proof.worldQuads.length,nativeScreenStripCases:proof.screenStrips.length,screenStripVertices,
 scope:'TH14 native modes 0..3 through draw dispatcher and batch boundary: visibility, pixel rounding, rotation, UV, gradients, inherited color and global tint. All 16 blend selectors and sampler states. Modes 8/9/13/14/15/16/17/19/20/21/23/24 and effect 8 submit native vertices and transforms, including mode 8 native anchor buffer initialization; real D3DX baseline plus SSE2 table executes. Retail 478a10 pretransformed strips used by curve lasers are compared across 16 blend selectors, visibility states, prior depth states and 2/12/240 input vertices. D3D calls and GPU batch/flush are recording sinks; final raster equivalence is not asserted.',
 wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmVm.hpp','cpp/game/AnmRenderer.hpp','tests/cpp/render-fixture.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-render-native.py','tools/th14-render-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-render-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.quads.length} TH14 quad cases, ${vertices} submitted vertices, ${proof.materials.length*3} materials, ${proof.strips.length} strips / ${stripVertices} vertices, ${proof.shapes.length} shapes / ${shapeVertices} vertices, ${proof.worldQuads.length} world quads.`);
