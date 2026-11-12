import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/display-mode-entry-nov12');
const sha=b=>createHash('sha256').update(b).digest('hex');
const nativeRaw=read(resolve(home,'context-native-v2/report.json')),native=JSON.parse(nativeRaw);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-display-context-native-nov12.py'))));
assert.equal(native.cases,12);assert.equal(native.wordsPerStage,37);
const build=JSON.parse(read(resolve(home,'context-component/build.json')));
for(const [name,digest]of Object.entries({...build.sourceBindings,...build.objectBindings}))assert.equal(sha(read(resolve(root,name))),digest,name);
const bytes=read(resolve(home,'context-component/candidate.wasm'));assert.equal(sha(bytes),build.wasmSha256);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport,env:{memory}});wasi.initialize(instance);
const c=instance.exports;let words=0;
for(const row of native.rows){
 assert.equal(c.run(row.mode,row.resource),111);
 const actual=Array.from(new Uint32Array(memory.buffer,c.output_ptr(),111));
 const expected=row.stages.flat();
 assert.deepEqual(actual,expected,`mode=${row.mode},resource=${row.resource}`);words+=actual.length;
}
const result={nativeCases:12,stagesPerCase:3,comparedWords:words,differentWords:0,
 actualCompositorResetAndBegin:true,normalGameProviders:141,fixtureOnlyRelaxedAccess:true,
 gpuServicesDeclared:true,screenMatrixMathNotCompared:true,syntheticInitialPlayOrigin:true,
 nativeReportSha256:sha(nativeRaw),wasmSha256:sha(bytes),checkerSha256:sha(read(import.meta.filename)),
 applicationOrPixelsAccepted:false,canonicalEngineChanged:false,completeGame:false};
write(resolve(home,'context-component/checked.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));
