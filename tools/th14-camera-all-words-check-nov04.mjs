import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-render-dimensions-nov04'),sha=b=>createHash('sha256').update(b).digest('hex');
const nativeRaw=read(resolve(home,'all-words-native.json')),native=JSON.parse(nativeRaw),dimensionsRaw=read(resolve(home,'reference/native.json')),dimensions=JSON.parse(dimensionsRaw);
assert(native.all75CameraWordsMapped&&native.cases===76&&native.referenceReadBlockExecutions===456);
assert(dimensions.verifiedOriginalRenderDimensionDataFlow&&dimensions.dimensionWords===64&&dimensions.screenMatrixMathSkipped);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-camera-all-words-native-nov04.py'))));
assert.equal(dimensions.toolSha256,sha(read(resolve(root,'tools/th14-camera-render-dimensions-native-nov04.py'))));
const buildRaw=read(resolve(home,'component/observer-build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(home,'component/observer.wasm'));
assert.equal(sha(wasm),build.wasmSha256);for(const obj of build.objectBindings)assert.equal(sha(read(obj.path)),obj.sha256);
for(const[path,digest]of Object.entries(build.fixtureDependencyHashes))assert.equal(sha(read(path)),digest);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const bytes=fn=>{const result=Buffer.alloc(300);for(let i=0;i<75;i++)result.writeUInt32LE(fn(i)>>>0,i*4);return result;};
const cppToNative=[...Array.from({length:18},(_,i)=>i),21,...Array.from({length:51},(_,i)=>i+24),18,19,20,22,23];assert.equal(cppToNative.length,75);
let comparedPrefixWords=0,referenceWords=0;
for(let cut=0;cut<=75;cut++){
 assert.equal(c.publication_case(cut,0),1);const actual=bytes(c.publication_word);
 for(let word=0;word<75;word++){
  const index=cppToNative[word],expected=index===12?(index<cut?0:0xbf800000):((index<cut?0x40000000:0x3f000000)+index)>>>0;
  assert.equal(actual.readUInt32LE(word*4),expected,`native word ${index}, prefix ${cut}`);++comparedPrefixWords;
 }
 assert.equal(sha(actual),native.rows[cut].mappedSemanticCppSha256);
 assert.deepEqual(Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0),[76,1,0,75,75,0,0]);
 for(let i=0;i<6;i++){assert.equal(c.publication_reference(i)>>>0,native.rows[cut].cameraReferenceBits[i]);++referenceWords;}
 assert.equal(sha(bytes(c.publication_final_word)),native.rows[75].mappedSemanticCppSha256);
}
const failureCuts=[0,13,19,22,23,24,73,74,75];
for(const cut of failureCuts){
 assert.equal(c.publication_case(cut,1),0);assert.equal(sha(bytes(c.publication_final_word)),native.rows[cut].mappedSemanticCppSha256);
 assert.deepEqual(Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0),[cut+1,1,0,cut,75,1,0]);
}
let resetWords=0;
for(const row of dimensions.rows){
 assert.equal(c.reset_dimensions(row.width,row.height,Number(row.entry===0x4465e0)),1);
 for(let camera=0;camera<4;camera++)for(let axis=0;axis<2;axis++){
  assert.equal(c.reset_dimension_word(camera,axis)>>>0,row.dimensionWords[camera][axis]);++resetWords;
 }
}
const result={verifiedAllCameraWordMapping:true,nativePrefixCases:76,mappedWordsPerPrefix:75,comparedPrefixWords,wrongWords:0,referenceReadWords:referenceWords,
 nativeResetProfiles:dimensions.profiles,resetDimensionWords:resetWords,failureCases:failureCuts.length,nativeDimensionWordIndices:[22,23],unmappedNativeWordIndices:[],
 syntheticInputsAndSchedule:true,screenMatrixMathNotAcceptedByDimensionReference:true,wholeGameplayCameraTailNotCaptured:true,productionIntegrated:false,
 physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,wasmSha256:build.wasmSha256,buildSha256:sha(buildRaw),nativePrefixProofSha256:sha(nativeRaw),
 nativeDimensionProofSha256:sha(dimensionsRaw),checkerSha256:sha(read(import.meta.filename))};
write(resolve(home,'component-verified.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(result));
