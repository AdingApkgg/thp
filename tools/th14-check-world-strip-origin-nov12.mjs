import assert from 'node:assert/strict';import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/world-strip-origin-nov12'),sha=b=>createHash('sha256').update(b).digest('hex');
const nativeRaw=read(resolve(H,'native.json')),native=JSON.parse(nativeRaw),build=JSON.parse(read(resolve(H,'component/build.json')));
assert.equal(native.toolSha256,sha(read(resolve(R,'tools/th14-world-strip-origin-native-nov12.py'))));
assert.equal(native.contextReportSha256,sha(read(resolve(R,'artifacts/th14/display-mode-entry-nov12/context-native-v2/report.json'))));
assert.equal(native.executableSha256,sha(read('H:/Games/th/14/th14.exe')));assert.equal(native.cases,216);
assert.equal(build.fixtureSha256,sha(read(resolve(R,'tools/th14-world-strip-origin-component-nov12.cpp'))));
for(const [n,h]of Object.entries(build.sourceBindings))assert.equal(sha(read(resolve(build.sourceRoot,n))),h,n);
for(const row of [...build.currentProviders,...build.baselineProviders])assert.equal(sha(read(resolve(R,row.object))),row.objectSha256,row.object);
const results={};
for(const label of ['candidate','baseline']){
 const bytes=read(resolve(H,`component/${label}.wasm`));assert.equal(sha(bytes),build.modules[label]);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport,env:{memory}});wasi.initialize(instance);const c=instance.exports;
 const result={cases:0,words:0,differentWords:0,differentCases:0,firstDifferences:[]};
 for(const row of native.rows){
  assert.equal(c.run(row.width,row.flags,row.parent,...row.position,row.route),1,JSON.stringify(row));
  const actual=Array.from(new Uint32Array(memory.buffer,c.output_ptr(),16));let count=0;
  for(let i=0;i<16;++i)if(actual[i]!==row.words[i]){++count;if(result.firstDifferences.length<6)result.firstDifferences.push({width:row.width,flags:row.flags,parent:row.parent,route:row.route,position:row.position,field:i,actual:actual[i],expected:row.words[i]});}
  ++result.cases;result.words+=16;result.differentWords+=count;if(count)++result.differentCases;
 }
 results[label]=result;
}
const passed=results.candidate.differentWords===0,oldCodeControlRejected=results.baseline.differentWords>0;
const report={passed,oldCodeControlRejected,results,normalProviders:141,fixtureNormalAccess:true,actualRendererDispatchModes:[23,24,'effect8'],
 nativeOriginalTranslationPrefix:true,nativeWholeCallback:false,upstreamNativeScaleAndRotationProducerNotCompared:true,
 scope:'Resource-present compositor Begin contexts at640x480/960x720/1280x960; no arbitrary play-origin or original pixels claim.',
 nativeReportSha256:sha(nativeRaw),candidateWasmSha256:build.modules.candidate,checkerSha256:sha(read(import.meta.filename)),completeGame:false};
write(resolve(H,'component/checked.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));assert(passed);assert(oldCodeControlRejected);
