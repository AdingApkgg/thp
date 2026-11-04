import assert from'node:assert/strict';import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/perspective-publication-nov04'),sha=b=>createHash('sha256').update(b).digest('hex');
const nr=read(resolve(root,'artifacts/th14/perspective-publication-native-cpu-nov04/verified.json')),native=JSON.parse(nr),br=read(resolve(home,'component/observer-build.json')),b=JSON.parse(br),wasm=read(resolve(home,'component/observer.wasm'));
assert(native.verifiedOriginalPerspectiveBoundariesAndWorkerCopy&&native.actualWindowsX86D3dxServices&&native.dllServicesDelegatedToActualReferenceCpu&&native.rows.length===24);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-perspective-publication-native-cpu-nov04.py'))));assert.equal(b.wasmSha256,sha(wasm));
for(const row of b.objectBindings)assert.equal(sha(read(row.path)),row.sha256);
for(const[path,digest]of Object.entries(b.fixtureDependencyHashes))assert.equal(sha(read(path)),digest);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const first=[],allCounts={};let wrongWords=0,failedCases=0,failures=0;
for(let profile=0;profile<4;profile++){
 assert.equal(c.perspective_case(profile,0,0),1);assert.deepEqual(Array.from({length:4},(_,i)=>c.perspective_meta(i)>>>0),[6,0,292,0]);
 for(let point=0;point<6;point++){
  assert.equal(c.perspective_seen(point),1);const row=native.rows.find(r=>r.profile===profile&&r.point===point),expected=Buffer.from(row.mappedCppHex,'hex');let wrong=0;
  for(let word=0;word<73;word++){const actual=c.perspective_word(point,word)>>>0,want=expected.readUInt32LE(word*4);if(actual!==want){wrong++;allCounts[word]=(allCounts[word]??0)+1;if(first.length<18)first.push({profile,point,word,actual,expected:want});}}
  wrongWords+=wrong;if(wrong)failedCases++;
 }
 for(let cut=0;cut<6;cut++){
  assert.equal(c.perspective_case(profile,cut,1),1);assert.deepEqual(Array.from({length:4},(_,i)=>c.perspective_meta(i)>>>0),[cut+1,1,292,0]);failures++;
  for(let word=0;word<73;word++)assert.equal(c.perspective_final_word(word)>>>0,c.perspective_word(cut,word)>>>0);
 }
}
const report={verifiedOriginalPerspectiveComponent:wrongWords===0,profiles:4,boundariesPerProfile:6,comparedMappedWords:24*73,wrongWords,failedCases,allCounts,first,failureCases:failures,nativeProofSha256:sha(nr),componentBuildSha256:sha(br),componentWasmSha256:sha(wasm),matrixInternalStoresNotModeled:true,unknownNativeWordsStillUnaccepted:[22,23],originalScheduleRecovered:false,completeGame:false,nativeEquivalent:false,checkerSha256:sha(read(import.meta.filename))};
write(resolve(home,'component-cpu-comparison.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));assert.equal(wrongWords,0);
