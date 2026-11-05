// Actual SceneCamera/read job, with an independent worker reading while one
// C++ Wasm call continually publishes synthetic words. No game assets.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {Worker} from 'node:worker_threads';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]),modules=resolve(process.argv[3]);
for(const path of [home,modules])assert(path.startsWith(resolve(root,'artifacts/th14')+'/')||path.startsWith(resolve(root,'artifacts/th14')+'\\'));
const sha=data=>createHash('sha256').update(data).digest('hex');
const buildRaw=readFileSync(resolve(home,'build.json')),build=JSON.parse(buildRaw),bytes=readFileSync(resolve(home,'component.wasm'));
assert.equal(sha(bytes),build.wasmSha256);
const moduleRaw=readFileSync(resolve(modules,'build.json')),moduleBuild=JSON.parse(moduleRaw);
for(const [name,row]of Object.entries(moduleBuild.sharedSceneModuleFiles))assert.equal(sha(readFileSync(resolve(modules,name))),row.sha256);
const {Th14SharedSceneCopy,SceneCopyWords:w}=await import(pathToFileURL(resolve(modules,'Th14SharedSceneCopy.mjs')));
const memory=new WebAssembly.Memory({initial:build.sharedMemory.initialPages,maximum:build.sharedMemory.maximumPages,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),threads=[],errors=[];
let reader,readCalls=0,cppSpawns=0;
const {instance}=await WebAssembly.instantiate(bytes,{env:{memory},wasi_snapshot_preview1:wasi.wasiImport,
 wasi:{'thread-spawn':()=>{++cppSpawns;throw new Error('Unexpected C++ thread spawn');}},camera:{now_ms:()=>performance.now(),
 read:(source,layout,index,offset,destination)=>{
  ++readCalls;const offsets=Array.from(new Uint32Array(memory.buffer,layout,75));
  const status=reader.read(memory.buffer,source,offsets,index,offset);
  if(status===1)new Uint32Array(memory.buffer,destination,1)[0]=reader.value(index);return status;
 }}});
wasi.initialize(instance);const c=instance.exports;
const snapshot=()=>Array.from({length:75},(_,i)=>c.snapshot_word(i)>>>0);
assert.equal(c.reset_copy(),1);c.fill(0x12340000);assert.equal(c.default_copy(75,0),1);
assert.deepEqual(snapshot(),Array.from({length:75},(_,i)=>(0x12340000|i)>>>0));
assert.equal(c.reset_copy(),1);assert.equal(c.default_copy(16,0),0);assert.equal(c.copied_words(),16);
c.fill(0x34560000);assert.equal(c.default_copy(75,0),1);
assert.deepEqual(snapshot(),Array.from({length:75},(_,i)=>((i<16?0x12340000:0x34560000)|i)>>>0));
assert.equal(c.reset_copy(),1);assert.equal(c.default_copy(13,1),2);assert.equal(c.default_copy(75,0),2);assert.equal(c.copied_words(),13);
assert.equal(c.reset_copy(),1);c.fill(0);const privateBefore=snapshot();
function createWorker(url){
 const worker=new Worker(`const {parentPort,workerData}=require('node:worker_threads');
 globalThis.self={postMessage:data=>parentPort.postMessage(data),close:()=>parentPort.close()};
 import(workerData.url).then(()=>parentPort.on('message',data=>self.onmessage({data})));`,{eval:true,workerData:{url:url.href}});
 const terminal=new Promise(resolve=>worker.on('exit',resolve));threads.push(terminal);
 const facade={onmessage:null,onerror:null,terminal,postMessage:data=>worker.postMessage(data),terminate:()=>worker.terminate()};
 worker.on('message',data=>facade.onmessage?.({data}));worker.on('error',error=>facade.onerror?.({message:String(error)}));return facade;
}
reader=new Th14SharedSceneCopy({createWorker,onError:error=>errors.push(String(error))});
let task,iterations=0,captured=[],during=0;
try{
 assert(reader.prepare());task=reader.current;let watchdog;
 try{assert.equal(await Promise.race([task.prepared,new Promise((_,reject)=>{watchdog=setTimeout(()=>reject(new Error('Preparation watchdog')),5000);})]),true);}
 finally{clearTimeout(watchdog);}
 const source=c.source_pointer()>>>0,layout=Array.from(new Uint32Array(memory.buffer,c.layout_pointer()>>>0,75));
 assert.equal(new Set(layout).size,75);assert.equal(Math.max(...layout),296);
 assert([0,1].includes(reader.read(memory.buffer,source,layout,0,layout[0])));
 iterations=c.publish_for_ms(500)>>>0;assert(iterations>0);
 await task.worker.terminal;assert.equal(reader.read(memory.buffer,source,layout,0,layout[0]),1);
 captured=Array.from({length:75},(_,i)=>reader.value(i));
 for(let index=0;index<75;++index){
  assert.equal(c.source_word(index)>>>0,(0xdead0000|index)>>>0);assert.equal(captured[index]&255,index);
  const version=captured[index]>>>8;if(version!==0&&version!==0xdead00){assert(version<=iterations);++during;}
 }
 assert(during>0,'This trial did not capture a word published inside the blocking C++ call');
 assert.deepEqual(snapshot(),privateBefore,'Worker must not write the C++ destination');
 assert.equal(c.worker_copy(),1);assert.equal(c.copied_words(),75);assert.deepEqual(snapshot(),captured);
 assert.equal(readCalls,75);reader.cancel();c.fill(0x56780000);assert.equal(c.worker_copy(),1);assert.equal(readCalls,75);assert.deepEqual(snapshot(),captured);
 assert.equal(Atomics.load(task.state,w.copied),75);assert.equal(Atomics.load(task.state,w.status),2);
 assert.equal(errors.length,0);assert.equal(cppSpawns,0);
}finally{reader.cancel();}
const exits=await Promise.all(threads);
const result={actualSceneCameraAndCppReadJob:true,defaultSynchronous75WordsMatch:true,defaultWaitAndResume75WordsMatch:true,
 stickyDefaultReadFailureVerified:true,independentPhysicalLiveReadsDuringBlockingCppCall:true,
 concurrentSyntheticWords:75,wordsFromInsideBlockingCall:during,publisherGenerations:iterations,
 workerDoesNotWriteCppDestination:true,cppDestinationMatchesWorkerWords:75,completedCppJobDoesNotReread:true,
 perWordAcknowledgements:false,workersTerminal:exits.length,workerExitCodes:exits,cppThreadSpawns:cppSpawns,
 originalValuesOrAssetsUsed:false,ordinaryBrowserAccepted:false,originalSchedulingAccepted:false,completeGame:false,
 buildSha256:sha(buildRaw),moduleBuildSha256:sha(moduleRaw),wasmSha256:sha(bytes),toolSha256:sha(readFileSync(import.meta.filename))};
writeFileSync(resolve(home,'verified.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({actualCppLiveCapture:true,wordsFromInsideBlockingCall:during,workersTerminal:exits.length,completeGame:false}));
