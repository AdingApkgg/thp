import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/player-initialization-oracle-nov13');
const read=p=>readFileSync(p),load=p=>JSON.parse(read(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const build=load(resolve(home,'component/build.json')),nativeBytes=read(resolve(home,'native.json')),native=JSON.parse(nativeBytes);
for(const [p,h]of Object.entries({...build.sourceBindings,...build.objectBindings,...build.observerBindings}))assert.equal(sha(read(resolve(root,p))),h,p);
assert(build.normalAccessControl&&native.actualFullConstructor&&native.actualFullInitialize);
assert.equal(sha(read(resolve(root,'tools/th14-player-initialization-oracle-nov13.py'))),native.toolSha256);
assert.equal(sha(read('H:/Games/th/14/th14.exe')),native.originalSha256);
assert.equal(sha(read(resolve(root,'tools/th14-native-transition-resource-loader-nov09.py'))),native.loaderSha256);
const archive=load(resolve(root,'artifacts/archive-differential/th14.json'));
const wasm=read(resolve(home,'component/probe.wasm'));assert.equal(sha(wasm),build.wasmSha256);
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
let calls=0;const env={memory};
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{++calls;throw Error('Unexpected platform service '+i.name);};
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const rows=[];let words=0;
for(const n of native.rows){
 c.reset();
 for(const [kind,name]of ['ascii.anm',n.anm,n.sht].entries()){
  const raw=read(resolve(archive.extraction,name));assert.equal(sha(raw),n.resourceHashes[name]);
  const p=c.allocate(raw.length);new Uint8Array(memory.buffer,p,raw.length).set(raw);
  try{assert.equal(c.resource_open(kind,p,raw.length),1,name);}finally{c.release(p);}
 }
 const count=c.initialize(n.slot);assert.equal(count,504);
 const actual=Array.from(new Uint32Array(memory.buffer,c.data(),count));
 const header=[...n.header.slice(0,10),...n.header.slice(16,56),...Array(104).fill(0),...n.header.slice(10,16)]; const expected=[...n.words,...header,...n.body];assert.equal(expected.length,count);
 const fields=[...n.fields,...Array.from({length:160},(_,i)=>'shtHeader.word'+i),...n.bodyFields.map(f=>'body.'+f)];
 const differences=[];
 for(let i=0;i<count;i++)if(actual[i]!==expected[i])differences.push({field:fields[i],index:i,native:expected[i],cpp:actual[i]});
 rows.push({slot:n.slot,anm:n.anm,sht:n.sht,words:count,actual,differences});words+=count;c.close();
}
assert.equal(calls,0);
const report={passed:rows.every(r=>!r.differences.length),rows,words,normalAccessControl:true,
 originalWholeConstructorAndInitialize:true,actualCppPlayerFrameInitialize:true,
 noOriginalGameProcessOrGpuOrAudioDevice:true,platformCalls:0,physicalLoadingScheduleAccepted:false,completeGame:false,
 nativeSha256:sha(nativeBytes),buildSha256:sha(read(resolve(home,'component/build.json'))),runnerSha256:sha(read(import.meta.filename))};
writeFileSync(resolve(home,'mapped-result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({...report,rows:rows.map(({actual,...r})=>({...r,differences:r.differences.slice(0,12)}))}));
if(!report.passed)process.exitCode=1;
