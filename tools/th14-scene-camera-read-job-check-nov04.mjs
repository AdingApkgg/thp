import assert from'node:assert/strict';import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/scene-camera-read-job-nov04'),sha=b=>createHash('sha256').update(b).digest('hex');
const nativeRaw=read(resolve(home,'native.json')),native=JSON.parse(nativeRaw),buildRaw=read(resolve(home,'build/build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(home,'build/component.wasm'));
assert(native.verifiedRetailTwoRepInterleavings&&native.syntheticSchedules===64);assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-scene-camera-read-job-native-nov04.py'))));
assert.equal(sha(wasm),build.wasmSha256);for(const[path,digest]of Object.entries(build.dependencyHashes))assert.equal(sha(read(path)),digest);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const load=(old,next)=>{for(let word=0;word<75;word++){assert.equal(c.case_word(0,word,old.readUInt32LE(word*4)),1);assert.equal(c.case_word(1,word,next.readUInt32LE(word*4)),1);}assert.equal(c.copy_reset(),1);};
const snapshot=()=>{const bytes=Buffer.alloc(300);for(let word=0;word<75;word++)bytes.writeUInt32LE(c.snapshot_word(word)>>>0,word*4);return bytes;};
const compare=(old,next,published,copied,expected)=>{load(old,next);assert.equal(c.publish_prefix(published),1);assert.equal(c.copy_until(copied,0,0),copied===75?1:0);assert.equal(c.copy_meta(0),copied);assert.equal(c.publish_prefix(75),1);assert.equal(c.copy_until(75,0,0),1);assert(snapshot().equals(expected));assert.equal(c.copy_meta(0),75);assert.equal(c.copy_meta(2),75);assert.equal(c.copy_until(75,0,0),1);assert.equal(c.copy_meta(2),75);};
const old=Buffer.from(native.syntheticOldHex,'hex'),next=Buffer.from(native.syntheticNewHex,'hex');let words=0;
for(const row of native.rows){compare(old,next,row.publisherPrefix,row.readerPrefix,Buffer.from(row.resultHex,'hex'));words+=75;}
const actual=native.stage5;compare(Buffer.from(actual.oldHex,'hex'),Buffer.from(actual.newHex,'hex'),actual.publisherPrefix,actual.readerPrefix,Buffer.from(actual.copiedHex,'hex'));words+=75;
for(const cut of [0,1,13,15,74]){load(old,next);assert.equal(c.copy_until(cut,1,0),2);assert.equal(c.copy_meta(0),cut);assert.equal(c.copy_meta(1),1);assert.equal(c.copy_until(75,0,0),2);assert.equal(c.copy_meta(0),cut);assert.equal(c.copy_reset(),1);assert.equal(c.copy_until(75,0,0),1);assert(snapshot().equals(old));}
load(old,next);assert.equal(c.copy_until(75,0,1),1);assert.equal(c.copy_meta(3),1);assert.equal(c.copy_meta(2),75);
const proof={verifiedResumableCameraReadJob:true,syntheticNativeRepSchedules:64,actualStage5MixedCopyWords:75,comparedWords:words,wrongWords:0,failedReadCases:5,reentryCase:1,completedJobDoesNotReread:true,
 actualStage5ScheduleIsInferredNotExact:true,wasmSha256:build.wasmSha256,buildSha256:sha(buildRaw),nativeSha256:sha(nativeRaw),checkerSha256:sha(read(new URL(import.meta.url))),
 productionGameSessionIntegrated:false,originalStateValuesProvidedToGameSession:false,completeGame:false,nativeEquivalent:false};
write(resolve(home,'component-verified.json'),JSON.stringify(proof,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(proof));
