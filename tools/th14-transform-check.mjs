import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/transform-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-transform-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/transform-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th14-transform-fixture.cpp');
const wasm=resolve(out,'transforms.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
for(const row of proof.cases){
 const args=[...row.args];while(args.length<10)args.push(0);
 c.begin_case(row.op,row.refs,row.args.length,...args,row.x,row.y,row.z);
 for(const [frame,e] of row.timeline.entries()){
  const label=`op ${row.op} refs ${row.refs} frame ${frame}`;
  assert.equal(c.tick(),0,label+' return');
  const values=[...e.extra,...e.texture,...e.pivot,...e.scroll,...e.position,...e.physical,...e.rotation,...e.scale,...e.uvOffset,e.timer,...e.size,e.mode,e.counter];
  for(const [i,expected] of values.entries()){
   const actual=c.value(i);
   // Native uses SSE scalar floats; shared interpolation/libm may round once differently.
   assert.ok(Math.abs(actual-expected)<=Math.max(1e-6,Math.abs(expected)*2.4e-7),`${label} field ${i}: ${actual} != ${expected}`);
  }
  assert.equal(c.word(0)>>>0,e.primary,label+' primary');
  assert.equal(c.word(1)>>>0,e.secondary,label+' secondary');
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'Selected original TH14 interpreter transform/color timelines; no renderer, child-creation or complete-game equivalence.',
 nativeExecutableSha256:proof.executableSha256,timelines:proof.cases.length,frames:proof.cases.reduce((n,r)=>n+r.timeline.length,0),wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes','AnmGeometry','Rng','Timer','Interpolation'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-transform-native.py','tools/th14-transform-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-transform-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.timelines} original TH14 transform/color timelines (${report.frames} frames).`);
