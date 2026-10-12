import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/transform-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th13-transform-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/transform-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','AnmProjection','GraphicsMath','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th13-transform-fixture.cpp');
const wasm=resolve(out,'transforms.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=13',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
for(const row of proof.cases){
 const args=[...row.args];while(args.length<4)args.push(0);
 c.begin_case(row.op,row.refs,row.args.length,...args,row.x,row.y);
 for(const [frame,expected] of row.timeline.entries()){
  assert.equal(c.tick(),0,`op ${row.op} frame ${frame}`);
  const values=[...expected.extra,...expected.texture,...expected.pivot,...expected.scroll,expected.alpha];
  values.forEach((v,i)=>assert.equal(c.value(i),v,`op ${row.op} refs ${row.refs} frame ${frame} field ${i}`));
  expected.position.forEach((v,i)=>assert.ok(Math.abs(c.value(i+9)-v)<=Math.max(1e-6,Math.abs(v)*1.2e-7),`op ${row.op} frame ${frame} position ${i}: ${c.value(i+9)} != ${v}`));
  [...expected.physical,...expected.size,expected.mode,...expected.uvOffset].forEach((v,i)=>assert.equal(c.value(i+12),v,`op ${row.op} frame ${frame} shape field ${i}`));
 }
}
for(const row of proof.quads){
 assert.equal(c.quad_case(row.mode,row.ax,row.ay,row.parent),1);
 row.vertices.forEach((v,i)=>assert.ok(Math.abs(c.vertex(i)-v)<=Math.max(2e-5,Math.abs(v)*1.2e-7),
  `quad ${JSON.stringify(row)} component ${i}: ${c.vertex(i)} != ${v}`));
}
for(const row of proof.uvQuads){
 c.uv_case(...row.scale,...row.offset);
 assert.deepEqual(Array.from({length:8},(_,i)=>c.uv_value(i)),row.output,JSON.stringify(row));
}
for(const row of proof.rings){
 assert.equal(c.ring_case(row.op,row.count,row.parent,row.colorMode),0);
 assert.equal(c.ring_allocation(),row.allocation);
 row.vertices.forEach((v,i)=>v.forEach((value,f)=>{
  if(f===4)assert.equal(c.ring_color(i)>>>0,value);else assert.ok(Math.abs(c.ring_value(i,f)-value)<=Math.max(2e-5,Math.abs(value)*1.2e-7),`ring ${row.op}/${row.count}/${row.parent}/${row.colorMode} vertex ${i}/${f}: ${c.ring_value(i,f)} != ${value}`);
 }));
}
for(const row of proof.motion){
 c.motion_begin(row.rate,row.independentTime,row.camera);
 for(const [frame,expected] of row.timeline.entries()){
  assert.equal(c.tick(),0);assert.deepEqual(Array.from({length:expected.length},(_,i)=>c.motion_value(i)),expected,`motion ${JSON.stringify(row)} frame ${frame}`);
 }
}
for(const row of proof.ribbons){
 assert.equal(c.ribbon_begin(row.seed,row.rate),0);assert.equal(c.ring_allocation(),0x418);
 assert.deepEqual(Array.from({length:5},(_,i)=>c.ribbon_initial(i)),[row.initial.phase,...row.initial.position,row.initial.layer]);
 for(const [frame,expected] of row.timeline.entries()){
  assert.equal(c.tick(),0);assert.equal(c.ribbon_timer(),expected.timer);assert.deepEqual([c.ribbon_rng(0),c.ribbon_rng(1)], [expected.rng[0],expected.rng[2]]);
  assert.deepEqual(Array.from({length:48},(_,i)=>c.ribbon_step(i)),expected.steps,`ribbon steps seed ${row.seed} rate ${row.rate} frame ${frame}`);
  expected.vertices.forEach((v,i)=>v.forEach((value,f)=>{
   if(f===3)assert.equal(c.ribbon_color(i)>>>0,value);else assert.equal(c.ribbon_value(i,f),value,`ribbon ${row.seed}/${row.rate}/${frame} vertex ${i}/${f}`);
  }));
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'Original full ANM interpreter transform timelines and 2-D quad functions; not complete animation/render equivalence.',
 nativeExecutableSha256:proof.executableSha256,timelines:proof.cases.length,frames:proof.cases.reduce((n,r)=>n+r.timeline.length,0),quads:proof.quads.length,uvQuads:proof.uvQuads.length,rings:proof.rings.length,motionTimelines:proof.motion.length,ribbonTimelines:proof.ribbons.length,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes','AnmGeometry','Rng','Timer','Interpolation'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th13-transform-native.py','tools/th13-transform-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-transform-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.timelines} native transform timelines (${report.frames} frames), ${report.quads} quads, ${report.rings} rings, ${report.motionTimelines} motion and ${report.ribbonTimelines} ribbon timelines.`);
