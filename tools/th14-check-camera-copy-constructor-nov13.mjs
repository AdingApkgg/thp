import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-copy-constructor-nov13');
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const build=load(resolve(home,'component-v2/build.json')),native=load(resolve(home,'native.json'));
assert(build.normalAccessControl&&native.actualRetailCameraCopyAndReset);
assert.equal(native.originalInstructionBytesPatched,0);
assert.equal(sha(read(resolve(root,'tools/th14-camera-copy-constructor-native-nov13.py'))),native.bindings['tools/th14-camera-copy-constructor-native-nov13.py']);
for(const [p,h]of Object.entries({...build.sourceBindings,...build.objectBindings}))assert.equal(sha(read(resolve(root,p))),h,p);
const bytes=read(resolve(home,'component-v2/probe.wasm'));assert.equal(sha(bytes),build.wasmSha256);
assert.equal(sha(read(resolve(home,'component-v2/fixture.cpp'))),build.fixtureSha256);
const module=await WebAssembly.compile(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const errors=[],pool=new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}),env={memory};let platformCalls=0;
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{++platformCalls;throw Error('Unexpected platform call '+i.name);};
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
const instance=await WebAssembly.instantiate(module,{env,wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>pool.spawn(arg)}});
wasi.initialize(instance);await pool.prewarm();const c=instance.exports;
const wait=async f=>{const until=performance.now()+5000;while(!f()){assert(performance.now()<until,'Thread pool return timeout');assert.equal(errors.length,0,errors.join('\n'));await new Promise(r=>setTimeout(r,1));}};
const rows=[],differences=[];let exception=null;
try{
 for(const n of native.rows)for(let stage=1;stage<=6;++stage){
  await wait(()=>pool.slot.ready&&!pool.slot.busy);
  new Uint32Array(memory.buffer,c.input_data(),75).set(n.inputWords);
  const meta=Array.from(new Uint32Array(memory.buffer,c.run_case(n.mode,n.captureAfterMath,stage),8));
  assert.deepEqual(meta,[0,1,1,stage,1,n.mode,n.captureAfterMath,75]);
  const actual=Array.from(new Uint32Array(memory.buffer,c.output_data(),150));
  const expected=[...n.stageInitializedWords,...n.worldAfterMathWords];
  const first=differences.length;
  for(let i=0;i<150;++i)if(actual[i]!==expected[i])differences.push({pose:n.poseIndex,mode:n.mode,captureAfterMath:n.captureAfterMath,stage,field:i<75?'stage'+i:'world'+(i-75),native:expected[i],cpp:actual[i]});
  rows.push({pose:n.poseIndex,mode:n.mode,captureAfterMath:n.captureAfterMath,stage,comparedWords:150,differentWords:differences.length-first});
 }
 await wait(()=>pool.slot.ready&&!pool.slot.busy);
}catch(e){exception=String(e?.stack??e);}finally{await pool.shutdown();}
assert.equal(errors.length,0,errors.join('\n'));assert.equal(platformCalls,0);
const tasks=pool.summary(),physical=pool.physicalSummary();
const retired=tasks.every(t=>t.returned&&!t.error)&&physical.every(t=>t.closed&&t.exitCode===0);
const report={passed:!exception&&!differences.length&&rows.length===72&&retired,cases:rows.length,comparedWords:rows.length*150,
 differentWords:differences.length,exception,rows,normalAccessControl:true,actualCppLoadingWorker:true,
 actualStageOwnerCreationCaptureAndInitialize:true,normalGameObjectsVerifiedReused:141,
 nativeScope:'Unmodified40d412..40d502 copy/default-reset block, before callback registration',
 resourceBoundary:'Empty object storage and one placeholder STD instruction; no asset VM initialization',
 controlledCaptureBeforeOrAfterActualMath:true,completeArbitraryConcurrentStoreInterleavingsAccepted:false,
 physicalCopyTimestampOrWriterProven:false,originalFullConstructorAccepted:false,allTasksAndWorkersRetired:retired,
 tasks,physicalWorkers:physical,platformCalls,newGameOrGpuOrAudioStarted:false,
 productionChanged:false,strict35kCameraMismatchClosed:false,completeGame:false,
 bindings:{native:sha(read(resolve(home,'native.json'))),build:sha(read(resolve(home,'component-v2/build.json'))),runner:sha(read(import.meta.filename))}};
writeFileSync(resolve(home,'result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
writeFileSync(resolve(home,'private-differences.json'),JSON.stringify(differences,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({...report,rows:undefined,tasks:undefined,physicalWorkers:physical}));
if(!report.passed)process.exitCode=1;
