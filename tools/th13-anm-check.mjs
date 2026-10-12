// Compile only the ANM modules in a separate output directory, then compare the
// actual C++ interpreter with freshly executed original TH13 handler observations.
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/anm-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th13-anm-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/anm-native.json'),'utf8'));
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const sources=['AnmInterpreter','AnmVm','AnmGeometry','Interpolation','AnmResource'].map(s=>`cpp/game/${s}.cpp`);
const sha=b=>createHash('sha256').update(b).digest('hex');
const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing',
 '-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory'];
const results=[];
for(const title of [13,12]){
 const path=resolve(out,`th${title}.wasm`);
 execFileSync(compiler,[...flags,`-DPORT_TITLE=${title}`,...sources,'tests/cpp/th13-anm-fixture.cpp','-o',path],{
  cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 const c=instance.exports;
 let resources=0,scripts=0;
 if(title===13){
  for(const row of proof.cases){
   const label=`opcode=${row.op} value=${row.value} variant=${row.variant}`;
   assert.equal(c.run(row.op,row.value,row.variant,row.refs,row.arg,row.arg2),row.status,label+' return');
   const fields=['stopped','primary','secondary','layer','flags2','flipY','visible','scaleDirty','flag15','addressV','drawingMode','vertexColorMode'];
   fields.forEach((key,i)=>assert.equal(c.word(i)>>>0,Number(row[key]),label+' '+key));
   assert.equal(c.real(0),row.scaleY,label+' scaleY');
   // The native probe stops before the shared per-frame timer tick.
   assert.equal(c.real(1),row.timerFraction+(row.stopped?0:1),label+' timer');
   if(row.nextStatus!==null)assert.equal(c.next_update(),row.nextStatus,label+' next return');
  }
  assert.equal(c.canonical(5),64,'interrupt label must survive default-handler filtering');
  for(const row of proof.polar){
   assert.equal(c.run_polar(row.seed,row.low,row.high,row.refs,row.visual),0);
   for(const [i,key] of ['x','y'].entries()){
    const actual=c.polar_real(i,row.refs),expected=row[key];
    // x87 fsincos and WASM libm may differ in the final float rounding.
    assert.ok(Math.abs(actual-expected)<=Math.max(1e-6,Math.abs(expected)*1.2e-7),
     `polar ${JSON.stringify(row)} ${key}: ${actual} != ${expected}`);
   }
   assert.equal(c.rng_word(0),row.rngSeed);assert.equal(c.rng_word(1),row.rngCalls);
   assert.equal(c.rng_word(2),0,'visual RNG is not consumed');
  }
  const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th13.json'),'utf8'));
  const target=JSON.parse(readFileSync(resolve(root,'runtimes/th13/target.json'),'utf8'));
  assert.equal(archive.archiveSha256,sha(readFileSync(target.dataArchives['th13.dat'].path)));
  for(const row of archive.decoded.filter(f=>f.name.endsWith('.anm'))){
   const data=readFileSync(resolve(archive.extraction,row.name));assert.equal(sha(data),row.sha256);
   const p=c.allocate(data.length);assert.ok(p);
   try{
    new Uint8Array(c.memory.buffer,p,data.length).set(data);
    const count=c.open_resource(p,data.length);assert.ok(count>0,`${row.name}: loader result ${count}`);
    resources++;scripts+=count;
   }finally{c.release(p);}
  }
  assert.equal(resources,68,'all original TH13 ANM resources');
 }else{
  assert.equal(c.canonical(2),2);
  assert.equal(c.run(2,0,0,0,0),1,'TH12 opcode 2 keeps its own retirement behavior');
  assert.equal(c.next_update(),1);
  assert.equal(c.word(6),1,'TH12 stop does not clear visibility');
  assert.equal(c.run(68,3,0,0,3),0);
  assert.equal(c.word(3),3);assert.equal(c.word(4),0x800000,'TH12 layer does not acquire TH13 flags');
 }
 results.push({title,passed:true,wasmSha256:sha(bytes),resources,scripts});
}
const tracked=[...sources,...['AnmOpcodes','AnmVm','AnmResource','AnmGeometry','Interpolation','Timer','Rng','Types','PortTitle'].map(p=>`cpp/game/${p}.hpp`),'tests/cpp/th13-anm-fixture.cpp'];
const report={passed:true,scope:'Selected ANM instruction state and all resource loading; not complete gameplay or renderer equivalence.',
 nativeExecutableSha256:proof.executableSha256,nativeCases:proof.cases.length,randomPolarCases:proof.polar.length,results,
 sourceHashes:Object.fromEntries(tracked.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th13-anm-native.py','tools/th13-anm-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
writeFileSync(resolve(root,'docs/porting/th13-anm-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} state and ${proof.polar.length} random-polar cases; 68 ANM resources; TH12 stop/layer regression passed.`);
