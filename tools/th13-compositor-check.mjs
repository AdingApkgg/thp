import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/compositor-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th13-compositor-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/compositor-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const names=['AnmVm','AnmResource','AnmInterpreter','AnmManager','AnmGeometry','AnmProjection','AnmRenderer','GraphicsMath','Interpolation','SceneCamera','SceneCompositor'];
const sources=[...names.map(n=>`cpp/game/${n}.cpp`),'tests/cpp/th13-compositor-fixture.cpp'];
const results=[];
for(const title of [13,12]){
 const path=resolve(out,`th${title}.wasm`);
 execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
  '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
  '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',`-DPORT_TITLE=${title}`,...sources,'-o',path],
  {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 const c=instance.exports,archive=JSON.parse(readFileSync(resolve(root,`artifacts/archive-differential/th${title}.json`),'utf8'));
 const resource=readFileSync(resolve(archive.extraction,'text.anm')),resourceHash=sha(resource);
 assert.equal(resourceHash,archive.decoded.find(r=>r.name==='text.anm').sha256);
 const p=c.allocate(resource.length);new Uint8Array(c.memory.buffer,p,resource.length).set(resource);
 assert.equal(c.open_resource(p,resource.length),1);c.release(p);
 const scripts=Array.from({length:c.copy_count()},(_,i)=>c.copy_script(i));
 assert.deepEqual(scripts,title===13?proof.bindings.map(v=>v.script):[81,82,81]);
 if(title===13)for(const row of proof.cameras){
  c.camera_reset(Number(row.restricted));
  ['full','play','world'].forEach((key,i)=>assert.deepEqual(Array.from({length:6},(_,j)=>c.camera_value(i,j)),row[key]));
 }
 c.camera_reset(1);
 const copies=[];
 for(let i=0;i<c.pass_count();++i){
  const priority=c.pass_value(i,0),kind=c.pass_value(i,1);
  if(!((kind>=6&&kind<=13)||kind===21||kind===22))continue;
  assert.equal(c.draw_pass(i),1);
  const native=title===13?proof.callbacks.find(v=>v.priority===priority):null;
  if(title===13){
   assert(native,`unobserved compositor priority ${priority}`);
   const expected=native.events.filter(e=>e.kind==='target'||e.kind==='clear');
   assert.equal(c.event_count(),expected.length);
   expected.forEach((e,j)=>{
    assert.equal(c.event_value(j,0),e.kind==='target'?0:1);
    if(e.kind==='target')assert.equal(c.event_value(j,1),e.target===99?0:e.target+1);
    else{
     assert.equal(c.event_value(j,2)>>>0,e.color);assert.equal(c.event_value(j,3),e.rectangle?1:0);
     if(e.rectangle){const [x,y,right,bottom]=e.rectangle;assert.deepEqual([4,5,6,7].map(f=>c.event_value(j,f)),[x,y,right-x,bottom-y]);}
    }
   });
   assert.equal(c.draw_count(),native.events.filter(e=>e.kind==='copy').length);
  }
  for(let j=0;j<c.draw_count();++j)copies.push(Array.from({length:7},(_,k)=>c.draw_value(j,k)));
 }
 if(title===13){
  // Target and sampled texture differ for every copy, including the newly
  // restored 2 -> 3 -> screen steps. Coordinates come from original text.anm.
  assert.deepEqual(copies.map(v=>v.slice(0,5)),[[4,3,2,127.5,15.5],[3,4,2,127.5,15.5],[4,3,2,127.5,15.5],[0,4,2,31.5,15.5]]);
  for(let y=0;y<3;++y)for(let x=0;x<3;++x){
   assert.equal(c.anchor_case(x,y),0);
   assert.deepEqual(Array.from({length:4},(_,i)=>Array.from({length:5},(_,f)=>c.anchor_vertex(i,f))),proof.anchorVertices.slice((y*3+x)*4,(y*3+x+1)*4));
   assert.deepEqual([12,13,14].map(i=>c.world_component(i)),[17,29,41],'anchor is not applied after rotation');
  }
  for(const row of proof.addressing)for(const initial of [[1,1],[2,3],[3,2]]){
   assert.equal(c.address_case(row.u,row.v,...initial),0);
   const expected=[...initial];
   for(const event of row.events){assert.equal(event.sampler,0);expected[event.state-1]=event.value;}
   assert.deepEqual([c.address_value(0),c.address_value(1)],expected,`sampler ${row.u}/${row.v} from ${initial}`);
  }
  for(const row of proof.worldTransforms){
   assert.equal(c.transform_case(row.parent,row.rootOffset,row.depthFlag),0);
   assert.deepEqual([c.transform_depth()],row.depthWrites,`world depth flag ${row.depthFlag}`);
   for(const matrix of row.matrices){
    assert.ok(matrix.state===256||matrix.state===16);
    assert.deepEqual(Array.from({length:16},(_,i)=>matrix.state===256?c.world_component(i):c.texture_component(i)),matrix.values,`native 3D matrix ${JSON.stringify(row)}`);
   }
   assert.equal(row.matrices.length,2);
  }
  for(const row of [...proof.rectangles,...proof.circles]){
   assert.equal(c.rectangle_case(row.mode,row.ax||0,row.ay||0,row.parent,row.segments||0),0);
   assert.equal(c.draw_count(),row.draws.length);assert.equal(row.draws.length,row.mode>=20?2:1);
   row.draws.forEach((draw,d)=>{
    assert.equal(draw.topology,row.mode===16?6:row.mode===17?3:5);assert.equal(draw.count,row.segments||2);assert.equal(draw.stride,20);
    draw.vertices.forEach((vertex,v)=>{
     for(let f=0;f<4;++f){const actual=c.rectangle_component(d,v,f),expected=vertex[f];assert.ok(Math.abs(actual-expected)<=Math.max(2e-5,Math.abs(expected)*1.2e-7),`rectangle ${JSON.stringify(row)} ${d}/${v}/${f}: ${actual} != ${expected}`);}
     assert.equal(c.rectangle_color(d,v)>>>0,vertex[4]);
    });
   });
  }
  for(const row of proof.vertexColors){
   assert.equal(c.color_case(row.mode,row.tinted),0);assert.equal(c.draw_count(),1);
   assert.deepEqual([0,1,2,1,2,3].map((_,i)=>c.rectangle_color(0,i)>>>0),[0,1,2,1,2,3].map(i=>row.colors[i]));
  }
  for(const row of proof.ribbonDraws){
   assert.equal(c.ribbon_draw_case(row.parent,row.rootOffset,row.depth),0);assert.equal(c.draw_count(),1);
   assert.deepEqual(Array.from({length:6},(_,i)=>c.draw_metadata(0,i)),[30,4,24,row.depth,1,1]);
   for(const matrix of row.events.filter(e=>e.kind==='matrix'))assert.deepEqual(Array.from({length:16},(_,i)=>matrix.state===256?c.world_component(i):c.texture_component(i)),matrix.values);
   const draw=row.events.find(e=>e.kind==='rectangle');assert.equal(draw.topology,5);assert.equal(draw.count,30);assert.equal(draw.stride,24);
   draw.vertices.forEach((vertex,v)=>vertex.forEach((value,f)=>assert.equal(f===3?c.world_vertex_color(v)>>>0:c.rectangle_component(0,v,f),value)));
   assert.deepEqual(row.events.filter(e=>e.kind==='state'&&(e.state===28||e.state===14)).map(e=>[e.state,e.value]),[[28,1],[14,row.depth],[28,0]]);
  }
 }
 const first=title===13?31:29;
 for(const layer of [0,first-2,first-1])assert.equal(c.layer_case(layer,0),layer);
 for(const layer of [0,first,first+1])assert.equal(c.layer_case(layer,1),layer===first+1?first+1:first);
 results.push({title,passed:true,copies,resourceHash,wasmSha256:sha(bytes)});
}
const report={passed:true,nativeExecutableSha256:proof.executableSha256,
 scope:'Original Supervisor copy bindings, camera resets, target/copy callbacks, samplers, shape vertices, gradients and effect-5 draw state; matrix comparisons use zero rotations. No full-stage pixel or gameplay equivalence claim.',
 nativeCallbacks:proof.callbacks.length,nativeAnchorVertices:proof.anchorVertices.length,nativeAddressingCases:proof.addressing.length,nativeWorldTransforms:proof.worldTransforms.length,nativeRectangles:proof.rectangles.length,nativeCircles:proof.circles.length,nativeVertexColors:proof.vertexColors.length,nativeRibbonDraws:proof.ribbonDraws.length,results,
 sourceHashes:Object.fromEntries([...sources,'cpp/game/SceneSchedule.hpp','cpp/game/SceneCompositor.hpp','cpp/game/AnmManager.hpp','cpp/game/AnmRenderer.hpp','cpp/game/AnmVm.hpp','cpp/game/AnmGeometry.hpp','cpp/game/GameSession.cpp','cpp/game/StageDraw.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th13-compositor-native.py','tools/th13-compositor-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-compositor-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: four copies, ten compositor callbacks, ${report.nativeRectangles} rectangles, ${report.nativeCircles} circles, ${report.nativeRibbonDraws} ribbon draws; TH12 regression.`);
