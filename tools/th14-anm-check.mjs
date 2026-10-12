// TH14 has its own dispatch/flags. Reuse only the C++ fixture's observation API.
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/anm-check');
mkdirSync(out,{recursive:true});
nativePython('tools/th14-anm-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/anm-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmInterpreter','AnmVm','AnmGeometry','Interpolation','AnmResource'].map(s=>`cpp/game/${s}.cpp`);
const fixture='tests/cpp/th13-anm-fixture.cpp',wasm=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing',
 '-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',
 '-DPORT_TITLE=14',...sources,fixture,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,
 env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});
wasi.initialize(instance);const c=instance.exports;
const fields=['stopped','primary','secondary','layer','flags2','flipY','visible','scaleDirty','flag15','addressV','drawingMode','vertexColorMode','blendMode','depthDisabled','flipX','anchorX','anchorY'];
for(const row of proof.cases){
 const label=`TH14 op=${row.op} value=${row.value} variant=${row.variant} refs=${row.refs}`;
 assert.notEqual(c.canonical(row.op),65535,label+' mapped');
 assert.equal(c.run(row.op,row.value,row.variant,row.refs,row.arg,row.arg2),row.status,label+' status');
 fields.forEach((key,i)=>assert.equal(c.word(i)>>>0,Number(row[key]),label+' '+key));
 assert.equal(c.real(0),row.scaleY,label+' scaleY');
 assert.equal(c.real(2),row.scaleX,label+' scaleX');
 assert.equal(c.real(1),row.timerFraction+(row.stopped?0:1),label+' timer');
 if(row.nextStatus!==null)assert.equal(c.next_update(),row.nextStatus,label+' next status');
}
assert.equal(c.canonical(5),64,'TH14 interrupt label');
for(const op of [609,610])assert.ok(c.canonical(op)!==0&&c.canonical(op)!==65535,`TH14 ${op} has a real geometry handler, not the TH13 default`);
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'),'utf8'));
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8'));
assert.equal(archive.archiveSha256,sha(readFileSync(target.dataArchives['th14.dat'].path)));
const resources=[];
for(const row of archive.decoded.filter(f=>f.name.endsWith('.anm'))){
 const data=readFileSync(resolve(archive.extraction,row.name));assert.equal(sha(data),row.sha256);
 const p=c.allocate(data.length);assert.ok(p);
 try{
  new Uint8Array(c.memory.buffer,p,data.length).set(data);
  const result=c.open_resource(p,data.length);
  assert.ok(result>0||result===-18,`${row.name}: unexpected format error ${result}`);
  resources.push({name:row.name,sha256:row.sha256,result});
 }finally{c.release(p);}
}
const tracked=[...sources,...['AnmOpcodes','AnmVm','AnmResource','AnmGeometry','Interpolation','Timer','Rng','Types','PortTitle'].map(p=>`cpp/game/${p}.hpp`),fixture];
const report={passed:true,scope:'Selected native ANM state only. Unimplemented instructions reject resource loading; no complete animation/gameplay claim.',
 nativeExecutableSha256:proof.executableSha256,nativeCases:proof.cases.length,wasmSha256:sha(bytes),
 resources,loadedResources:resources.filter(r=>r.result>0).length,blockedResources:resources.filter(r=>r.result===-18).length,
 sourceHashes:Object.fromEntries(tracked.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-anm-native.py','tools/th14-anm-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
writeFileSync(resolve(root,'docs/porting/th14-anm-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} native TH14 states; ${resources.length} resources audited (${report.loadedResources} loaded, ${report.blockedResources} explicitly blocked).`);
