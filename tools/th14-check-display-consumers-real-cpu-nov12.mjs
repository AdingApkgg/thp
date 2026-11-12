import assert from 'node:assert/strict';import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/display-consumers-nov12'),O=resolve(H,'real-cpu-native');
const sha=b=>createHash('sha256').update(b).digest('hex'),raw=read(resolve(O,'deformation-native.json')),native=JSON.parse(raw);
assert.equal(native.toolSha256,sha(read(resolve(R,'tools/th14-display-consumers-real-cpu-native-nov12.py'))));
assert.equal(native.parentToolSha256,sha(read(resolve(R,'tools/th14-display-consumers-native-nov12.py'))));
assert.equal(native.derivedToolSha256,sha(read(resolve(O,'derived-native.py'))));
assert.equal(native.normalizationWorkerSourceSha256,sha(read(resolve(R,native.normalizationWorkerSource))));
assert.equal(native.normalizationWorkerExeSha256,sha(read(resolve(O,'normalize-worker.exe'))));
assert.equal(native.normalizationWorkerCompilerSha256,sha(read('C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe')));
assert.equal(native.executableSha256,sha(read('H:/Games/th/14/th14.exe')));
assert.equal(native.dllSha256,sha(read('C:/Windows/SysWOW64/d3dx9_43.dll')));
assert(native.realD3dxNormalizeExecutedOnCpu&&native.normalizationWorkerExited&&native.originalDeformationInstructionsUnmodified);
assert.equal(native.normalizationWorkerExitCode,0);assert.equal(native.normalizationCalls,8928);
const build=JSON.parse(read(resolve(H,'component/build.json')));
for(const [n,h]of Object.entries(build.sourceBindings))assert.equal(sha(read(resolve(build.sourceRoot,n))),h,n);
for(const row of build.currentProviders)assert.equal(sha(read(resolve(R,row.object))),row.objectSha256,row.object);
const bytes=read(resolve(H,'component/candidate.wasm'));assert.equal(sha(bytes),build.modules.candidate);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport,env:{memory}});wasi.initialize(instance);
const c=instance.exports,actual=n=>Array.from(new Uint32Array(memory.buffer,c.output_ptr(),n));
let rectangleWords=0,updateWords=0,differentWords=0;const differences=[];
function compare(want,input){const got=actual(want.length);for(let i=0;i<want.length;++i)if(got[i]!==want[i]){++differentWords;if(differences.length<16)differences.push({input,field:i,actual:got[i],expected:want[i]});}}
for(const row of native.rectangles){assert.equal(c.rectangle(row.width,...row.rectangle),2890);compare(row.words,[row.width,...row.rectangle]);rectangleWords+=2890;}
for(const row of native.updates){c.begin(row.width,...row.position,row.radius,row.rate);for(const [frame,f]of row.frames.entries()){
 assert.equal(c.tick(),2893);compare([...f.words,...f.state],[row.width,...row.position,row.radius,row.rate,frame]);updateWords+=2893;
}}
const result={passed:differentWords===0,rectangleCases:native.rectangles.length,rectangleWords,updateTimelines:native.updates.length,
 updateFrames:native.updates.reduce((n,r)=>n+r.frames.length,0),updateWords,differentWords,differences,
 fullWavePositionsAcceptedForThisComponent:differentWords===0,normalizationCalls:native.normalizationCalls,
 normalizationService:native.normalizationService,originalGameInheritedFloatingPointEnvironmentMeasured:false,
 originalDeformationCodeUnmodified:true,realCpuMathServiceDeclared:true,normalizationValuesSuppliedToCpp:false,
 retainedUnicornNormalizeComparisonDifferentWords:178,nativeReportSha256:sha(raw),candidateWasmSha256:sha(bytes),
 checkerSha256:sha(read(import.meta.filename)),fullGameOrPixelsAccepted:false,completeGame:false};
write(resolve(O,'checked.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));assert(result.passed);
