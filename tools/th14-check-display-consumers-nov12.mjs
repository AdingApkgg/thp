import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/display-consumers-nov12');
const sha=b=>createHash('sha256').update(b).digest('hex');
const build=JSON.parse(read(resolve(H,'component/build.json'))),nativeRaw=read(resolve(H,'deformation-native.json'));
const native=JSON.parse(nativeRaw),fadeRaw=read(resolve(H,'fade-native/native.json')),fades=JSON.parse(fadeRaw);
assert.equal(sha(read(resolve(R,'tools/th14-display-consumers-native-nov12.py'))),native.toolSha256);
assert.equal(sha(read(resolve(R,'tools/th14-stage-fade-render-native.py'))),native.fadeParentSha256);
assert.equal(sha(read(resolve(H,'fade-native-derived.py'))),native.fadeDerivedSha256);
assert.equal(sha(read(resolve(R,'tools/th14-display-consumers-component-nov12.cpp'))),build.fixtureSha256);
assert.equal(sha(read('H:/Games/th/14/th14.exe')),native.executableSha256);
assert.equal(sha(read('C:/Windows/SysWOW64/d3dx9_43.dll')),native.dllSha256);
for(const [n,h]of Object.entries(build.sourceBindings))assert.equal(sha(read(resolve(build.sourceRoot,n))),h,n);
for(const row of [...build.currentProviders,...build.baselineProviders])assert.equal(sha(read(resolve(R,row.object))),row.objectSha256,row.object);
const floatBits=x=>new Uint32Array(new Float32Array([x]).buffer)[0];
const results={};
for(const label of ['candidate','baseline']){
 const bytes=read(resolve(H,`component/${label}.wasm`));assert.equal(sha(bytes),build.modules[label]);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport,env:{memory}});wasi.initialize(instance);
 const c=instance.exports,output=n=>Array.from(new Uint32Array(memory.buffer,c.output_ptr(),n));
 const stats={fadeCases:0,fadeWords:0,fadeDifferences:0,rectangleCases:0,rectangleWords:0,rectangleDifferences:0,
  updateTimelines:0,updateFrames:0,updateWords:0,updateDifferences:0,updateConsumerWords:0,updateConsumerDifferences:0,
  wavePositionDifferences:0,firstDifferences:[],firstWaveDifferences:[]};
 function diff(a,b,kind,input,field){if(stats.firstDifferences.length<12)stats.firstDifferences.push({kind,input,field,actual:a,expected:b});}
 for(const row of fades.rows){
  assert.equal(c.fade(...row.input),26);const actual=output(26),expected=[...row.vertices,...row.viewport.slice(0,4),...row.viewport.slice(4).map(floatBits)];
  ++stats.fadeCases;stats.fadeWords+=26;
  for(let i=0;i<26;++i)if(actual[i]!==expected[i]){++stats.fadeDifferences;diff(actual[i],expected[i],'fade',row.input,i);}
 }
 for(const row of native.rectangles){
  assert.equal(c.rectangle(row.width,...row.rectangle),2890);const actual=output(2890);
  ++stats.rectangleCases;stats.rectangleWords+=2890;
  for(let i=0;i<2890;++i)if(actual[i]!==row.words[i]){++stats.rectangleDifferences;diff(actual[i],row.words[i],'rectangle',[row.width,...row.rectangle],i);}
 }
 for(const row of native.updates){
  c.begin(row.width,...row.position,row.radius,row.rate);++stats.updateTimelines;
  for(const [frame,expected]of row.frames.entries()){
   assert.equal(c.tick(),2893);const actual=output(2893),wanted=[...expected.words,...expected.state];
   ++stats.updateFrames;stats.updateWords+=2893;
   for(let i=0;i<2893;++i){
    // Source coordinates, color, reciprocal-W, UV and enemy fields do not use D3DX normalization/sine.
    const consumer=i>=2890||![3,4,5].includes(i%10);if(consumer)++stats.updateConsumerWords;
    if(actual[i]!==wanted[i]){++stats.updateDifferences;if(consumer)++stats.updateConsumerDifferences;else ++stats.wavePositionDifferences;
     if(!consumer&&stats.firstWaveDifferences.length<8)stats.firstWaveDifferences.push({input:[row.width,...row.position,row.radius,row.rate,frame],field:i,actual:actual[i],expected:wanted[i]});
     diff(actual[i],wanted[i],'update',[row.width,...row.position,row.radius,row.rate,frame],i);}
   }
  }
 }
 results[label]=stats;
}
const candidate=results.candidate,baseline=results.baseline;
const passed=candidate.fadeDifferences===0&&candidate.rectangleDifferences===0&&candidate.updateConsumerDifferences===0;
const controlRejected=baseline.fadeDifferences>0&&baseline.rectangleDifferences>0&&baseline.updateConsumerDifferences>0;
const report={passed,controlRejected,results,nativeReportSha256:sha(nativeRaw),fadeReportSha256:sha(fadeRaw),
 modules:build.modules,normalAccess:true,normalProviders:141,realD3dxDllExecutedUnderUnicorn:true,
 originalInheritedFloatingPointEnvironmentMeasured:false,fullWavePositionsAccepted:candidate.wavePositionDifferences===0,
 realGpuOrPixelsAccepted:false,wholeGameAccepted:false,completeGame:false,checkerSha256:sha(read(import.meta.filename))};
write(resolve(H,'component/checked.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));assert(passed,'candidate display consumers');assert(controlRejected,'old-code negative control');
