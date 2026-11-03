import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-word-publication-nov04'),sha=b=>createHash('sha256').update(b).digest('hex');
const nativeRaw=read(resolve(root,'artifacts/th14/camera-publication-prefix-nov04/native-v2.json')),native=JSON.parse(nativeRaw),buildRaw=read(resolve(home,'component-build/observer-build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(home,'component-build/observer.wasm'));
assert(native.verifiedOriginalCameraPublicationWordPrefix&&native.cases===76&&!native.oldFailureClosed);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-camera-publication-copy-native-nov04.py'))));assert.equal(sha(wasm),build.wasmSha256);
for(const obj of build.objectBindings)assert.equal(sha(read(obj.path)),obj.sha256);
for(const[path,digest]of Object.entries(build.fixtureDependencyHashes))assert.equal(sha(read(path)),digest);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const bytes=fn=>{const b=Buffer.alloc(292);for(let i=0;i<73;i++)b.writeUInt32LE(fn(i)>>>0,i*4);return b;};
const metas=[];for(let cut=0;cut<=73;cut++){
 assert.equal(c.publication_case(cut,0),1);assert.equal(sha(bytes(c.publication_word)),native.rows[cut].workerMappedCameraSha256);
 const meta=Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0);assert.deepEqual(meta,[74,1,0,73,73,0,0]);metas.push(meta);
 assert.equal(sha(bytes(c.publication_final_word)),native.rows[75].workerMappedCameraSha256);
}
assert.equal(c.publication_case(74,0)>>>0,0xffffffff);assert.equal(c.publication_case(0,2)>>>0,0xffffffff);
const failures=[];for(const cut of[0,13,73]){assert.equal(c.publication_case(cut,1),0);assert.equal(sha(bytes(c.publication_final_word)),native.rows[cut].workerMappedCameraSha256);const state=Array.from({length:7},(_,i)=>c.publication_meta(i)>>>0);assert.deepEqual(state,[cut+1,1,0,cut,73,1,1]);failures.push({cut,state});}
const expected=[
 [1,4,1,0,0,0,0,0],[1,5,1,1,0,0,0,0],[0,8,1,0,0,0,0,0],[0,8,1,1,0,0,0,0],[1,5,1,1,0,0,2,0],
 [1,3,0,0,0,0,0,0],[0,8,0,0,0,0,0,0],[0,7,0,0,0,0,0,0],[1,6,0,0,0,0,0,0],[1,5,2,1,0,0,0,0]];
const loader=[];for(let mode=0;mode<10;mode++){assert.equal(c.scene_poll_case(mode),1);const state=Array.from({length:8},(_,i)=>c.scene_poll_word(i)>>>0);assert.deepEqual(state,expected[mode]);loader.push({mode,state});}
const result={verifiedMappedCameraPrefixesAndSceneOnlyPolling:true,mappedCameraDwords:73,nativePublicationDwords:75,nativeOpaqueTailDwordsNotAccepted:2,mappedPrefixCases:74,publicationFailureCases:failures,loaderProtocolCases:loader,unmodeledIndexRejected:true,nativeValuesProvidedToEngine:false,syntheticComponentInputs:true,oldCameraFailureClosed:false,completeGame:false,nativeEquivalent:false,nativeProofSha256:sha(nativeRaw),buildSha256:sha(buildRaw),wasmSha256:sha(wasm),driverSha256:sha(read(import.meta.filename))};
write(resolve(home,'component-verified.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,publicationFailureCases:failures.length,loaderProtocolCases:loader.length}));
