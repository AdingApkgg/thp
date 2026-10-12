import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/compositor-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-compositor-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/compositor-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmManager','AnmGeometry','AnmProjection','AnmRenderer','GraphicsMath','Interpolation','SceneCamera','SceneCompositor'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-compositor-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'),'utf8'));
const resource=readFileSync(resolve(archive.extraction,'text.anm')),resourceHash=sha(resource);
assert.equal(resourceHash,archive.decoded.find(r=>r.name==='text.anm').sha256);
const p=c.allocate(resource.length);new Uint8Array(c.memory.buffer,p,resource.length).set(resource);assert.equal(c.open_resource(p,resource.length),1);c.release(p);
const modes=[];
for(const row of proof.cameras){
 assert.equal(c.initialize(row.width,row.height),1);
 const bindings=Array.from({length:4},(_,i)=>c.copy_script(i));
 assert.deepEqual(bindings,row.bindings.map(v=>v.script));
 row.viewports.forEach((v,i)=>assert.deepEqual(Array.from({length:6},(_,f)=>c.camera_value(i,f)),v));
 modes.push({width:row.width,height:row.height,bindings,filters:Array.from({length:4},(_,i)=>c.copy_filter(i))});
}
assert.equal(c.initialize(640,480),1);
const passes=Array.from({length:c.pass_count()},(_,i)=>({i,priority:c.pass_value(i,0),kind:c.pass_value(i,1),layer:c.pass_value(i,2)}));
assert.deepEqual(passes.map(v=>v.priority),passes.map(v=>v.priority).sort((a,b)=>a-b));
assert.equal(new Set(passes.map(v=>v.priority)).size,passes.length);
const animation=passes.filter(v=>v.kind===0);
assert.deepEqual(animation.map(v=>[v.priority,v.layer]),proof.animation.map(v=>[v.priority,v.events.find(e=>e.kind==='layer').layer]).sort((a,b)=>a[0]-b[0]));
const copyDraws=[];let checked=0;
for(const pass of passes){
 const native=[...proof.callbacks,...proof.animation].find(v=>v.priority===pass.priority);
 if(!native)continue;
 assert.equal(c.draw_pass(pass.i),1,`draw priority ${pass.priority}`);
 const expected=native.events.filter(e=>e.kind==='target'||e.kind==='clear');
 assert.equal(c.event_count(),expected.length,`target events at ${pass.priority}`);
 expected.forEach((e,j)=>{
  assert.equal(c.event_value(j,0),e.kind==='target'?0:1);
  if(e.kind==='target')assert.equal(c.event_value(j,1),e.target===99?0:e.target+1);
  else{
   assert.equal(c.event_value(j,2)>>>0,e.color);assert.equal(c.event_value(j,3),e.rectangle?1:0);assert.equal(c.event_value(j,8),e.flags);
   if(e.rectangle){const [x,y,right,bottom]=e.rectangle;assert.deepEqual([4,5,6,7].map(f=>c.event_value(j,f)),[x,y,right-x,bottom-y]);}
  }
 });
 const viewports=native.events.filter(e=>e.kind==='viewport').map(e=>e.viewport);
 assert.deepEqual(Array.from({length:c.viewport_count()},(_,j)=>Array.from({length:6},(_,f)=>c.viewport_value(j,f))),viewports,`viewports at ${pass.priority}`);
 const draws=native.events.filter(e=>e.kind==='copy'||e.kind==='layer');
 assert.equal(c.draw_count(),draws.length,`submissions at ${pass.priority}`);
 draws.forEach((e,j)=>{
  if(e.kind==='copy'){
   assert.equal(c.draw_alpha(j),0,`alpha test on copy ${e.copy}`);assert.equal(c.alpha_restored(),1);
   assert.equal(c.copy_color(e.copy)>>>0,0xffffffff);
   copyDraws.push({copy:e.copy,draw:Array.from({length:7},(_,k)=>c.draw_value(j,k))});
  }
 });
 ++checked;
}
assert.equal(checked,42);assert.equal(copyDraws.length,4);
assert.deepEqual(copyDraws.map(v=>v.draw.slice(0,2)),[[4,3],[3,4],[4,3],[0,4]]);
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativeCompositorCallbacks:proof.callbacks.length,nativeAnimationCallbacks:proof.animation.length,
 scope:'Retail callback registration, four copy bindings at three display modes, camera viewports, layer ordering and target clear masks. Real text.anm is interpreted for copy draws; GPU/projection, alternate callback pointers and complete gameplay are outside this comparison.',
 modes,copyDraws,resourceHash,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/SceneSchedule.hpp','cpp/game/SceneCompositor.hpp','cpp/game/AnmManager.hpp','cpp/game/AnmRenderer.hpp','cpp/game/ZunGraphics.hpp','cpp/game/GameSession.cpp','cpp/game/StageDraw.cpp','cpp/sdl/GraphicsDevice.cpp','tests/cpp/render-fixture.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-compositor-native.py','tools/th14-compositor-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-compositor-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: 3 display modes, 4 copy draws, ${checked} native TH14 compositor / ANM callbacks.`);
