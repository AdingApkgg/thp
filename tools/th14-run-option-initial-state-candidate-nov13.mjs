import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/option-refresh-oracle-nov13');
const read=p=>readFileSync(p),load=p=>JSON.parse(read(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const build=load(resolve(home,'candidate-component/build.json')),nativeBytes=read(resolve(home,'native.json')),native=JSON.parse(nativeBytes);
assert(build.normalAccessControl&&native.actualFullConstructor&&native.actualFullInitialize);
assert.equal(sha(read(resolve(root,'tools/th14-option-refresh-native-nov13.py'))),native.toolSha256);
for(const [p,h]of Object.entries({...build.sourceBindings,...build.objectBindings,...build.observerBindings}))assert.equal(sha(read(resolve(root,p))),h,p);
const wasm=read(resolve(home,'candidate-component/probe.wasm'));assert.equal(sha(wasm),build.wasmSha256);
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),env={memory};let platformCalls=0;
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{++platformCalls;throw Error('Unexpected platform service '+i.name);};
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=load(resolve(root,'artifacts/archive-differential/th14.json')),rows=[];let comparedWords=0;
for(const n of native.rows){
 c.reset();for(const [kind,name]of ['ascii.anm',n.anm,n.sht].entries()){
  const raw=read(resolve(archive.extraction,name));assert.equal(sha(raw),n.resourceHashes[name]);
  const p=c.allocate(raw.length);new Uint8Array(memory.buffer,p,raw.length).set(raw);
  try{assert.equal(c.resource_open(kind,p,raw.length),1,name);}finally{c.release(p);}
 }
 assert.equal(c.initialize(n.slot),504);c.observer_begin();
 for(const [index,action]of n.sequence.entries()){
  const stage=n.stages[index];assert.equal(stage.label,action.label);
  const length=c.action({refresh:0,stage:1,tick:2}[action.kind],action.power);assert(length,'Actual action failed '+n.slot+' '+action.label);
  const actual=Array.from(new Uint32Array(memory.buffer,c.data(),length));
  const expected=[...stage.head,...stage.state,...stage.clocks,...stage.options,...stage.history,...stage.vms,stage.hudCalls];
  const differences=[];
  if(length!==expected.length)differences.push({field:'snapshotLength',native:expected.length,cpp:length});
  const field=i=>i<5?['vmCount','scriptSeed','scriptCalls','visualSeed','visualCalls'][i]:i<9?['lifeState','optionCount','optionAngle','focused'][i-5]:i<29?'clock'+Math.floor((i-9)/5)+'.'+['previous','current','fraction','ratePresent','flags'][(i-9)%5]:i<149?'option'+Math.floor((i-29)/15)+'.word0x'+n.optionOffsets[(i-29)%15].toString(16):i<215?'history'+(i-149):i===expected.length-1?'hudCalls':'vm'+Math.floor((i-215)/303)+'.'+n.bodyFields[(i-215)%303];
  for(let i=0;i<Math.min(length,expected.length);i++)if(actual[i]!==expected[i])differences.push({index:i,field:field(i),native:expected[i],cpp:actual[i]});
  comparedWords+=expected.length;rows.push({slot:n.slot,label:action.label,power:action.power,kind:action.kind,comparedWords:expected.length,
   nativeVmCount:stage.head[0],cppVmCount:actual[0],actual,differences});
 }
 c.close();
}
assert.equal(platformCalls,0);
const report={passed:rows.every(r=>!r.differences.length),selections:native.rows.length,steps:rows.length,comparedWords,
 differentSteps:rows.filter(r=>r.differences.length).length,differentWords:rows.reduce((sum,r)=>sum+r.differences.length,0),rows,
 actualNativeOptionFactoryAndStageReset:true,actualOriginalAnmFactoryInterpreterRegistryAndRetirement:true,
 declaredPowerAndTickSequence:true,rawHandlesAndRegistryOrderCompared:true,normalAccessControl:true,
 platformCalls,physicalLoadingScheduleAccepted:false,wholeGameAccepted:false,completeGame:false,
 bindings:{native:sha(nativeBytes),build:sha(read(resolve(home,'candidate-component/build.json'))),runner:sha(read(import.meta.filename))}};
writeFileSync(resolve(home,'candidate-result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({...report,rows:rows.filter(r=>r.differences.length).map(({actual,...r})=>({...r,differences:r.differences.slice(0,8)})).slice(0,12)}));
if(!report.passed)process.exitCode=1;
