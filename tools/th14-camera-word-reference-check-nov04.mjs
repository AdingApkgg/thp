import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-word-publication-v2-nov04'),sha=b=>createHash('sha256').update(b).digest('hex');
const nativeRaw=read(resolve(root,'artifacts/th14/camera-publication-prefix-nov04/native-reference.json')),native=JSON.parse(nativeRaw);
assert(native.verifiedOriginalCameraPublicationWordPrefix&&native.originalAnmCameraReadsExecutedAtEveryPrefix&&native.cases===76&&native.referenceReadBlockExecutions===456);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-camera-publication-reference-native-nov04.py'))));
const expectedLoader=[
 [1,4,1,0,0,0,0,0],[1,5,1,1,0,0,0,0],[0,8,1,0,0,0,0,0],[0,8,1,1,0,0,0,0],[1,5,1,1,0,0,2,0],
 [1,3,0,0,0,0,0,0],[0,8,0,0,0,0,0,0],[0,7,0,0,0,0,0,0],[1,6,0,0,0,0,0,0],[1,5,2,1,0,0,0,0]];
async function check(directory,prior){
 const buildRaw=read(resolve(home,directory,'observer-build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(home,directory,'observer.wasm'));assert.equal(sha(wasm),build.wasmSha256);
 for(const obj of build.objectBindings)assert.equal(sha(read(obj.path)),obj.sha256);
 for(const[path,digest]of Object.entries(build.fixtureDependencyHashes))assert.equal(sha(read(path)),digest);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const bytes=fn=>{const b=Buffer.alloc(292);for(let i=0;i<73;i++)b.writeUInt32LE(fn(i)>>>0,i*4);return b;};
 let referenceWrongWords=0,referenceWrongCases=0;const first=[];
 for(let cut=0;cut<=73;cut++){
  assert.equal(c.publication_case(cut,0),1);assert.equal(sha(bytes(c.publication_word)),native.rows[cut].workerMappedCameraSha256);
  assert.deepEqual(Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0),[74,1,0,73,73,0,0]);
  assert.equal(sha(bytes(c.publication_final_word)),native.rows[75].workerMappedCameraSha256);
  let wrong=0;for(let i=0;i<6;i++){const actual=c.publication_reference(i)>>>0,expected=native.rows[cut].cameraReferenceBits[i];if(actual!==expected){++wrong;if(first.length<4)first.push({cut,field:i,actual,expected});}}
  referenceWrongWords+=wrong;if(wrong)++referenceWrongCases;
 }
 for(const cut of[0,13,73]){assert.equal(c.publication_case(cut,1),0);assert.equal(sha(bytes(c.publication_final_word)),native.rows[cut].workerMappedCameraSha256);assert.deepEqual(Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0),[cut+1,1,0,cut,73,1,prior?1:0]);}
 assert.equal(c.publication_case(74,0)>>>0,0xffffffff);
 for(let mode=0;mode<10;mode++){assert.equal(c.scene_poll_case(mode),1);assert.deepEqual(Array.from({length:8},(_,i)=>c.scene_poll_word(i)>>>0),expectedLoader[mode]);}
 return {buildSha256:sha(buildRaw),wasmSha256:sha(wasm),sourceHashes:build.sourceHashes,referenceWrongWords,referenceWrongCases,first};
}
const candidate=await check('component-reference',false),prior=await check('component-reference-prior',true);
assert.equal(candidate.referenceWrongWords,0);assert.equal(candidate.referenceWrongCases,0);assert.equal(prior.referenceWrongCases,74);
assert.deepEqual(Object.keys(candidate.sourceHashes).filter(k=>candidate.sourceHashes[k]!==prior.sourceHashes[k]),['th12_web/cpp/game/Stage.cpp']);
const result={verifiedMappedPublicationAndLiveAnmCameraReferences:true,mappedPrefixCases:74,referenceFieldsPerPrefix:6,nativeReadBlockExecutions:456,candidateReferenceWrongWords:0,priorReferenceWrongWords:prior.referenceWrongWords,priorRejectedCases:prior.referenceWrongCases,publicationFailureCases:3,sceneOnlyProtocolCases:10,mappedCameraDwords:73,additionalNativeOpaqueDwordsNotAccepted:2,actualOldThreadScheduleRecovered:false,oldCameraFailureClosed:false,completeGame:false,nativeEquivalent:false,nativeProofSha256:sha(nativeRaw),candidateBuildSha256:candidate.buildSha256,priorBuildSha256:prior.buildSha256,candidateWasmSha256:candidate.wasmSha256,priorWasmSha256:prior.wasmSha256,driverSha256:sha(read(import.meta.filename))};
write(resolve(home,'reference-component-verified.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
