import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-native-order-nov04'),sha=b=>createHash('sha256').update(b).digest('hex');
const raw=read(resolve(home,'native.json')),native=JSON.parse(raw);
assert(native.namedFieldMapping&&native.cases===76&&native.referenceReadBlockExecutions===456);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-camera-native-order-native-nov04.py'))));
async function check(directory,prior){
 const br=read(resolve(home,directory,'observer-build.json')),b=JSON.parse(br),wasm=read(resolve(home,directory,'observer.wasm'));
 assert.equal(sha(wasm),b.wasmSha256);for(const obj of b.objectBindings)assert.equal(sha(read(obj.path)),obj.sha256);
 for(const[path,digest]of Object.entries(b.fixtureDependencyHashes))assert.equal(sha(read(path)),digest);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const bytes=fn=>{const r=Buffer.alloc(292);for(let i=0;i<73;i++)r.writeUInt32LE(fn(i)>>>0,i*4);return r;};
 let failedPrefixCases=0,wrongSemanticWords=0,wrongReferenceWords=0,wrongProgressCases=0;
 const first=[];
 for(let cut=0;cut<=75;cut++){
  assert.equal(c.publication_case(cut,0),1);
  const actual=bytes(c.publication_word),cppToNative=[...Array.from({length:18},(_,i)=>i),21,...Array.from({length:51},(_,i)=>i+24),18,19,20];
  assert.equal(cppToNative.length,73);let wrong=0;
  for(let word=0;word<73;word++){
   const index=cppToNative[word],expected=index===12?(index<cut?0:0xbf800000):((index<cut?0x40000000:0x3f000000)+index)>>>0;
   if(actual.readUInt32LE(word*4)!==expected){wrong++;if(first.length<8)first.push({cut,cppWord:word,nativeWord:index,actual:actual.readUInt32LE(word*4),expected});}
  }
  if(wrong)failedPrefixCases++;wrongSemanticWords+=wrong;
  if(!prior)assert.equal(sha(actual),native.rows[cut].mappedSemanticCppSha256);
  const meta=Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0);
  if(JSON.stringify(meta)!==JSON.stringify([76,1,0,75,73,0,0]))wrongProgressCases++;
  for(let i=0;i<6;i++)if((c.publication_reference(i)>>>0)!==native.rows[cut].cameraReferenceBits[i])wrongReferenceWords++;
  if(!prior)assert.equal(sha(bytes(c.publication_final_word)),native.rows[75].mappedSemanticCppSha256);
 }
 if(!prior){
  assert.equal(failedPrefixCases,0);assert.equal(wrongSemanticWords,0);assert.equal(wrongProgressCases,0);assert.equal(wrongReferenceWords,0);
  for(const cut of[0,13,19,22,23,24,73,74,75]){
   assert.equal(c.publication_case(cut,1),0);assert.equal(sha(bytes(c.publication_final_word)),native.rows[cut].mappedSemanticCppSha256);
   assert.deepEqual(Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0),[cut+1,1,0,cut,73,1,0]);
  }
 }else{assert(failedPrefixCases>0&&wrongSemanticWords>0);assert.equal(wrongProgressCases,76);}
 return {wasmSha256:b.wasmSha256,buildSha256:sha(br),failedPrefixCases,wrongSemanticWords,wrongReferenceWords,wrongProgressCases,first};
}
const candidate=await check('component',false),prior=await check('component-prior',true);
const result={verifiedNativeSemanticCameraOrder:true,nativeProgressCases:76,semanticMappedWordsPerPrefix:73,nativeReadBlockExecutions:456,unmappedNativeWordIndices:[22,23],unmappedWordsAreNotTrailing:true,candidate,priorPublishedCoreControl:prior,failureCases:9,oldFailuresClosed:false,completeGame:false,nativeEquivalent:false,nativeProofSha256:sha(raw),checkerSha256:sha(read(import.meta.filename))};
write(resolve(home,'component-verified.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
