import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-right-pair-nov12');
const sha=b=>createHash('sha256').update(b).digest('hex'),bindings={};
const read=path=>{const b=readFileSync(path);bindings[path.slice(root.length+1).replaceAll('\\','/')]={bytes:b.length,sha256:sha(b)};return b;};
const load=path=>JSON.parse(read(path));
const build=load(resolve(home,'component/build.json')),bytes=read(resolve(home,'component/probe.wasm'));
assert.equal(sha(bytes),build.wasmSha256);
assert.equal(sha(read(resolve(root,build.parentFullSessionBuildPath))),build.baseBuildSha256);
assert.equal(sha(read(resolve(home,'component/fixture.cpp'))),build.fixtureSha256);
const memory=new WebAssembly.Memory({initial:256,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{env:{memory},wasi_snapshot_preview1:wasi.wasiImport,
 wasi:{'thread-spawn':()=>{throw Error('Math-only component must not spawn a worker');}}});
wasi.initialize(instance);const c=instance.exports;
const run=(input,perspective)=>{new Uint8Array(memory.buffer,c.input_data(),300).set(input);c.compute(perspective?1:0);return Buffer.from(new Uint8Array(memory.buffer,c.output_data(),300));};
const rows=[];let positives=0;
for(const database of ['menu-camera-derived-nov06/native','camera-cached-derived-nov06/native-cpu']){
 const base=resolve(root,'artifacts/th14',database),native=load(resolve(base,'report.json'));
 const inputs=read(resolve(base,'inputs.u32')),expected=read(resolve(base,'expected.u32'));
 assert.equal(sha(inputs),native.inputsSha256);assert.equal(sha(expected),native.expectedSha256);
 assert.equal(inputs.length,native.rows.length*300);assert.equal(expected.length,inputs.length);
 for(let index=0;index<native.rows.length;index++){
  const info=native.rows[index],input=inputs.subarray(index*300,(index+1)*300),reference=expected.subarray(index*300,(index+1)*300);
  const result=run(input,info.mode==='perspective');assert(result.equals(reference),JSON.stringify({database,index,info}));
  const control=Buffer.from(input);control.writeFloatLE(control.readFloatLE(21*4)*.875,21*4);
  const altered=run(control,info.mode==='perspective');
  assert(!result.subarray(24*4,56*4).equals(altered.subarray(24*4,56*4)),'FOV control must change at least one matrix word');++positives;
  rows.push({database,index,mode:info.mode,all75WordsEqual:true,fovMatrixPositiveControl:true,resultSha256:sha(result)});
 }
}
const result={actualSceneCameraMethodsExecuted:true,cases:rows.length,all75WordsEqual:true,
 fovMatrixPositiveControls:positives,rows,buildSha256:sha(read(resolve(home,'component/build.json'))),
 bindings,toolSha256:sha(readFileSync(import.meta.filename)),rightVectorPublicationChanged:true,
 originalStoreOrderSeparatelyAudited:true,fullGpuOrWholeSchedulingAccepted:false,productionRootChanged:false,completeGame:false};
writeFileSync(resolve(home,'component/verified.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({cases:rows.length,all75WordsEqual:true,fovMatrixPositiveControls:positives,completeGame:false}));
