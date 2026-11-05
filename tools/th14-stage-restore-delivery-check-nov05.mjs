// Execute the production browser Worker entry and client through a Node facade.
// The synchronous Wasm component contains the actual GameSession initializer.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';
import {performance} from 'node:perf_hooks';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]),browser=resolve(process.argv[3]);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
for(const path of [home,browser])assert(path.startsWith(resolve(root,'artifacts/th14')+'\\')||path.startsWith(resolve(root,'artifacts/th14')+'/'));
const buildRaw=readFileSync(resolve(home,'build.json')),build=JSON.parse(buildRaw);
const browserRaw=readFileSync(resolve(browser,'build.json')),browserBuild=JSON.parse(browserRaw);
for(const [name,row]of Object.entries(browserBuild.independentRestoreModuleFiles))
 assert.equal(sha(readFileSync(resolve(browser,name))),row.sha256);
const {Th14StageRestoreDelivery}=await import(pathToFileURL(resolve(browser,'Th14StageRestoreDelivery.mjs')));
const {StageRestoreWords:w}=await import(pathToFileURL(resolve(browser,'Th14StageRestoreProtocol.mjs')));
const wasmBytes=readFileSync(resolve(home,'component.wasm'));assert.equal(sha(wasmBytes),build.wasmSha256);
const module=await WebAssembly.compile(wasmBytes),terminations=[],threads=[];
function createWorker(url){
 const worker=new Worker(`const {parentPort,workerData}=require('node:worker_threads');
globalThis.self={postMessage:message=>parentPort.postMessage(message),close:()=>parentPort.close()};
import(workerData.url).then(()=>parentPort.on('message',data=>self.onmessage({data})));`,
 {eval:true,workerData:{url:url.href}});
 const facade={onmessage:null,onerror:null,postMessage:data=>worker.postMessage(data),terminate:()=>{
  const completion=worker.terminate();terminations.push(completion);return completion;
 }};
 worker.on('message',data=>facade.onmessage?.({data}));
 worker.on('error',error=>facade.onerror?.({message:String(error)}));
 const terminal=new Promise(resolve=>worker.on('exit',code=>resolve(code)));threads.push(terminal);facade.terminal=terminal;
 return facade;
}
async function instance(ready,commit){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const wasm=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi.wasiImport,
  delivery:{ready,commit,now:()=>performance.now()}});wasi.initialize(wasm);return wasm.exports;
}
const cases=[];
for(const name of ['record','playback-a','playback-b','playback-c','cancel-after-script',
 'cancel-before-globals','reject-script-ack','reject-globals-ack','stale-generation']){
 const errors=[],client=new Th14StageRestoreDelivery({createWorker,onError:error=>errors.push(String(error))});
 const playback=name!=='record';assert.equal(client.begin(playback),true);
 const task=client.current;let commits=0,returned=false;
 const c=await instance(index=>client.ready(index),index=>{
  assert.equal(returned,false);++commits;
  if(name==='reject-script-ack'&&index===1)return 0;
  const accepted=client.committed(index);
  if((name==='cancel-after-script'&&index===1)||(name==='cancel-before-globals'&&index===2))client.cancel();
  if(name==='reject-globals-ack'&&index===3)return 0;
  return accepted?1:0;
 });
 if(name==='stale-generation')Atomics.add(task.state,w.generation,1);
 try{
  const progress=c.run(playback?1:0,2500);returned=true;
  const words=Array.from({length:13},(_,index)=>c.value(index)>>>0);
  const result={name,progress,stores:words[1],snapshots:words[2],invalid:words[3],
   snapshotWaits:words[4],iterations:words[5],score:words[6]|0,gameCalls:words[7],
   noError:words[8]===1,observerStillInstalled:words[9]!==0,elapsedUs:words[12],commitsBeforeReturn:commits};
  assert.equal(progress,words[0]);assert.equal(result.invalid,0);assert.equal(result.observerStillInstalled,false);
  if(name==='record'||name.startsWith('playback-')){
   assert.equal(progress,1);assert.equal(result.stores,3);assert.equal(result.snapshots,playback?1:0);
   assert.equal(commits,playback?4:3);assert.equal(result.score,playback?31415:-1000);
   assert.equal(result.gameCalls,0);assert.equal(result.noError,true);
   if(!playback){assert.equal(words[10],0x1011);assert.equal(words[11],0x1011);}
   let watchdog;
   try{await Promise.race([task.worker.terminal,new Promise((_,reject)=>{
    watchdog=setTimeout(()=>reject(new Error('Completed producer did not exit')),3000);
   })]);}finally{clearTimeout(watchdog);}
   assert.equal(Atomics.load(task.state,w.status),2);assert.equal(errors.length,0);
   result.producerCompletedNormallyBeforeCleanup=true;
  }else{
   assert.equal(progress,2);assert.equal(result.noError,false);
   const stores=name==='stale-generation'?0:(name==='cancel-after-script'||name==='reject-script-ack')?2:3;
   assert.equal(result.stores,stores);assert.equal(result.snapshots,name==='reject-globals-ack'?1:0);
   assert.equal(result.score,name==='reject-globals-ack'?31415:-1000);
   assert.equal(result.gameCalls,stores===3?0:19);
  }
  cases.push(result);
 }finally{client.cancel();}
}
// Replacing a task gets a distinct buffer; late old messages are ignored.
{
 const errors=[],client=new Th14StageRestoreDelivery({createWorker,onError:error=>errors.push(String(error))});
 assert(client.begin(false));const old=client.current,oldMessage=old.worker.onmessage;
 assert(client.begin(true));const next=client.current;
 assert.notEqual(next.state.buffer,old.state.buffer);assert.notEqual(next.generation,old.generation);
 oldMessage({data:{error:'stale task fault'}});assert.equal(errors.length,0);
 assert.equal(Atomics.load(old.state,w.command),2);assert.equal(client.ready(0),0);
 assert.equal(client.committed(1),false);client.cancel();assert.equal(client.ready(0),2);
 cases.push({name:'replacement-and-stale-message',passed:true});
}
// Paused/background main delivery must not turn a two-second gap into failure.
{
 const errors=[],client=new Th14StageRestoreDelivery({createWorker,onError:error=>errors.push(String(error))});
 assert(client.begin(true));const task=client.current;
 await new Promise(resolve=>setTimeout(resolve,2200));
 assert.equal(Atomics.load(task.state,w.status),1);assert.equal(client.ready(0),1);
 assert.equal(client.ready(1),2);assert.equal(client.committed(1),false);assert.equal(errors.length,0);
 client.cancel();cases.push({name:'paused-main-no-timeout',passed:true});
}
// Creation failure is visible and cannot silently use the old all-ready path.
{
 const errors=[],client=new Th14StageRestoreDelivery({createWorker:()=>{throw new Error('declared creation fault');},onError:error=>errors.push(String(error))});
 assert.equal(client.begin(true),false);assert.equal(errors.length,1);assert.equal(client.ready(0),2);
 cases.push({name:'worker-creation-failure',passed:true});
}
await Promise.all(terminations);await Promise.all(threads);
const result={schema:'th14/stage-restore-delivery-component/1',passed:true,cases,
 workerThreadsTerminal:threads.length,actualBrowserWorkerEntryThroughNodeFacade:true,
 realProductionClientAndProtocol:true,actualGameSessionInitializerBody:true,actualReplayEconomyProjection:true,
 syntheticInputsOnly:true,producerReceivesRngWordsOrFrameVmTargets:false,
 fourthSnapshotCommitAfterActualCopy:true,recordingUsesThreeOperations:true,playbackUsesFourOperations:true,
 retainedPartialStateOnAckFailure:true,ordinaryApplicationExecuted:false,
 extraAckSynchronizationCostUncalibrated:true,originalSchedulingEquivalent:false,completeGame:false,
 componentBuildSha256:sha(buildRaw),browserBuildSha256:sha(browserRaw),
 wasmSha256:build.wasmSha256,moduleBindings:browserBuild.independentRestoreModuleFiles,
 toolSha256:sha(readFileSync(import.meta.filename))};
const output=resolve(process.argv[4]??resolve(home,'verified.json'));
assert(output.startsWith(home+'\\')||output.startsWith(home+'/'));
writeFileSync(output,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,cases:cases.length,workerThreadsTerminal:threads.length,
 actualFourthSnapshotCopied:true,ordinaryApplicationExecuted:false,completeGame:false}));
