import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/particles-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-particles-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/particles-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmGeometry','AnmManager','AnmInterpreter','AnmResource','Interpolation'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-particles-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
let samples=0,maxAbsoluteError=0;
const close=(actual,expected,label)=>{const error=Math.abs(actual-expected);maxAbsoluteError=Math.max(maxAbsoluteError,error);assert.ok(error<=Math.max(.00008,Math.abs(expected)*.0000007),`${label}: ${actual} != ${expected}`);};
for(const row of proof.cases){
 const label=`seed ${row.seed}, rate ${row.rate}, slowdown ${row.slowdown}`;
 assert.equal(c.begin(row.seed,row.rate,row.slowdown),0);
 for(const [frame,v] of row.timeline.entries()){
  const where=`${label} frame ${frame}`;assert.equal(c.frame(frame),v.status,where+' status');
  assert.deepEqual(Array.from({length:400},(_,i)=>c.effect_word(i)),[...v.handles,...v.states],where+' handles/states');
  assert.deepEqual([c.rng(0),c.rng(1)],v.rng,where+' RNG');
  assert.deepEqual(Array.from({length:11},(_,i)=>c.effect_value(i)),[v.timer,...v.centers,v.rate],where+' controller');
  const expectedIds=new Set(v.children.map(ch=>ch.id));
  for(let id=1;id<=200;++id)assert.equal(c.exists(id),Number(expectedIds.has(id)),where+` child ${id} presence`);
  for(const child of v.children){
   const w=`${where} child ${child.id}`;
   assert.deepEqual(Array.from({length:7},(_,i)=>c.word(child.id,i)>>>0),[child.script,child.color,child.counter,child.age,child.visible,Number(child.stopped),child.duration],w+' state');
   const expected=[child.slowdown,...child.position,...child.interpolation,child.interpolationTimer];
   expected.forEach((value,i)=>close(c.value(child.id,i),value,w+` float ${i}`));++samples;
  }
  assert.equal(c.finish_frame(),0,where+' child update');
 }
}
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativeD3dxSha256:proof.d3dxSha256,nativeTimelines:proof.cases.length,
 nativeFrames:proof.cases.reduce((n,r)=>n+r.timeline.length,0),childSnapshots:samples,maxAbsoluteError,
 scope:'TH14 effect-7 spawning, two Hermite legs, RNG, slowdown, interrupt 1, missing handles and deletion. Native child binding/registry/allocation boundaries are controlled; real D3DX9_43 SSE2 normalization executes. Fixture update order is not a scheduler proof. Floating vector comparisons allow the recorded numerical tolerance.',wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmVm.hpp','cpp/game/AnmGeometry.hpp','cpp/game/AnmOpcodes.hpp','cpp/game/AnmManager.hpp','cpp/game/Rng.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-particles-native.py','tools/th14-particles-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-particles-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.nativeTimelines} native TH14 effect-7 timelines / ${report.nativeFrames} frames; ${samples} child snapshots (max float error ${maxAbsoluteError}).`);
