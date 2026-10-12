import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/ribbon-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-ribbon-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ribbon-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmGeometry','AnmManager','AnmInterpreter','AnmResource','Interpolation'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-ribbon-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const row of proof.cases){
 const label=`seed ${row.seed}, rate ${row.rate}, independent ${row.independent}`;
 assert.equal(c.begin(row.seed,row.rate,row.independent),0);
 assert.deepEqual(Array.from({length:5},(_,i)=>c.initial(i)),[row.initial.phase,...row.initial.position,row.initial.layer]);
 for(const [frame,v] of row.timeline.entries()){
  assert.equal(c.tick(frame),0);
  assert.deepEqual(Array.from({length:4},(_,i)=>c.state(i)),[...v.angles,v.timer,v.rate],`${label} frame ${frame} state`);
  assert.deepEqual(Array.from({length:4},(_,i)=>c.word(i)>>>0),[v.rng[0],v.rng[2],v.timerCurrent,v.timerPrevious],`${label} frame ${frame} timer/RNG`);
  assert.deepEqual(Array.from({length:120},(_,i)=>c.step(i)),v.steps,`${label} frame ${frame} steps`);
  for(const [i,vertex] of v.vertices.entries())for(const [f,want] of vertex.entries()){
   if(f===3)assert.equal(c.color(i)>>>0,want);
   else {const actual=c.vertex(i,f);assert.ok(Math.abs(actual-want)<=Math.max(0.000004,Math.abs(want)*0.00000024),`${label} frame ${frame} vertex ${i}/${f}: ${actual} != ${want}`);}
  }
 }
}
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativeTimelines:proof.cases.length,nativeFrames:proof.cases.reduce((n,r)=>n+r.timeline.length,0),
 scope:'TH14 effect-8 registration, initialization, pre-update, effective time rate, stopped VM callbacks and 80 generated vertices per frame. Allocation is a native boundary; device rendering and effect 7 are not asserted.',wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmVm.hpp','cpp/game/AnmGeometry.hpp','cpp/game/AnmOpcodes.hpp','cpp/game/AnmManager.hpp','cpp/game/Rng.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-ribbon-native.py','tools/th14-ribbon-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-ribbon-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.nativeTimelines} native TH14 effect-8 timelines / ${report.nativeFrames} frames.`);
