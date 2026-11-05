// Actual shared-memory GameSession integration. Fast cadence is a declared
// integration profile, not real-time original scheduling acceptance.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,openSync,closeSync,writeSync,statfsSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';
import {performance} from 'node:perf_hooks';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),options=new Map();
for(let index=2;index<process.argv.length;index+=2){
 assert(process.argv[index].startsWith('--')&&process.argv[index+1]);options.set(process.argv[index].slice(2),process.argv[index+1]);
}
const inside=path=>{const value=resolve(path),r=relative(resolve(root,'artifacts/th14'),value);assert(r&&!r.startsWith('..')&&!isAbsolute(r));return value;};
const home=inside(options.get('build')),browser=inside(options.get('browser-build')),
 assets=inside(options.get('assets')),native=inside(options.get('native')),out=inside(options.get('output'));
const maximumSeconds=Number(options.get('maximum-seconds')??5400);assert(maximumSeconds>=30&&maximumSeconds<=10800);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=path=>readFileSync(path),load=path=>JSON.parse(read(path));
const entry=options.get('entry')??'direct';assert(['direct','loading-title','queued-loading-title'].includes(entry));
const cadenceMode=options.get('cadence')??'real';assert(['real','fast'].includes(cadenceMode));
const maximumCallbacks=Number(options.get('maximum-callbacks')??300000);assert(Number.isInteger(maximumCallbacks)&&maximumCallbacks>=1&&maximumCallbacks<=300000);
const buildRaw=read(resolve(home,'build.json')),build=JSON.parse(buildRaw);
let coreBuild=build;
if(entry!=='direct'){
 assert(build.compiled&&build.gameObjectsReused===141&&build.actualGameSessionTitleAndAttractPath);
 const coreRaw=read(resolve(root,build.parentFullSessionBuildPath));assert.equal(sha(coreRaw),build.baseBuildSha256);coreBuild=JSON.parse(coreRaw);
}
assert(coreBuild.compiled&&coreBuild.gameUnitsRecompiled===141&&coreBuild.oldObjectsReused===0);
const wasmBytes=read(resolve(home,entry==='direct'?'session.wasm':'probe.wasm'));assert.equal(sha(wasmBytes),build.wasmSha256);
assert.equal(sha(read(resolve(home,'fixture.cpp'))),build.fixtureSha256);
const browserRaw=read(resolve(browser,'build.json')),browserBuild=JSON.parse(browserRaw);
assert.equal(sha(browserRaw),build.parentGlesBuildSha256);
assert(build.sharedWasmMemory);
for(const [name,row]of Object.entries(build.sharedSceneModuleFiles))assert.equal(sha(read(resolve(home,name))),row.sha256);
const {Th14SharedSceneCopy,SceneCopyWords:sw}=await import(pathToFileURL(resolve(home,'Th14SharedSceneCopy.mjs')));
const memory=new WebAssembly.Memory({initial:build.sharedMemory.initialPages,maximum:build.sharedMemory.maximumPages,shared:true});
assert(memory.buffer instanceof SharedArrayBuffer);
for(const [name,row]of Object.entries(browserBuild.independentRestoreModuleFiles))assert.equal(sha(read(resolve(browser,name))),row.sha256);
const {Th14StageRestoreDelivery}=await import(pathToFileURL(resolve(browser,'Th14StageRestoreDelivery.mjs')));
const {StageRestoreWords:w}=await import(pathToFileURL(resolve(browser,'Th14StageRestoreProtocol.mjs')));
const manifestRaw=read(resolve(assets,'manifest.json')),manifest=JSON.parse(manifestRaw);
assert(manifest.passed&&manifest.unchangedEntries===226);assert.deepEqual(manifest.changedEntries,['demo0.rpy']);
const replayPath=inside(manifest.replayPath),replay=read(replayPath),archive=read(resolve(assets,'th14.dat'));
assert.equal(sha(replay),manifest.replaySha256);assert.equal(sha(archive),manifest.referenceArchiveSha256);
const nativeReportRaw=read(resolve(native,'report.json')),nativeReport=JSON.parse(nativeReportRaw);
assert(nativeReport.childExited&&!nativeReport.error);assert.equal(nativeReport.sourceFullReplaySha256,manifest.replaySha256);
const expected=read(resolve(native,'selected-state.u32'));assert.equal(sha(expected),nativeReport.selectedSha256);
assert.equal(expected.length,nativeReport.callbacks*128);
const originalCamera=read(resolve(native,'world-camera.raw')),cameraTail=read(resolve(native,'world-camera-tail.u32')),
 originalHud=read(resolve(native,'hud-score.u32'));
assert.equal(originalCamera.length,nativeReport.callbacks*292);assert.equal(cameraTail.length,nativeReport.callbacks*8);
assert.equal(originalHud.length,nativeReport.callbacks*8);
const initialRaw=read(resolve(native,'untouched-first-player.json')),initial=JSON.parse(initialRaw);
for(const word of [initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie])assert(Number.isInteger(word)&&word>=0&&word<=0xffffffff);
mkdirSync(out);const timers=new Set(),threads=[],terminations=[],errors=[],completedTasks=[];
const rawPath=resolve(out,'observations.u32'),fd=openSync(rawPath,'wx');
const put=(name,value)=>writeFileSync(resolve(out,name),JSON.stringify(value,null,2)+'\n');
let c,started=false,lastEvents=0,observed=0,compared=0,displayFrames=0,lastProgress=0,stoppedBy='unknown';
const counts={},cameraCounts={},hudCounts={},stageCounts={},firstByStage={},stageEntries=[],taskStates=[],taskSnapshots=new Map();
let firstDifference=null,lastStage=0,finalMeta=[],exception=null;
const sceneTasks=[],sceneSnapshots=new Map();let cppThreadSpawns=0;
function sceneState(task){return {generation:task.generation,status:Atomics.load(task.state,sw.status),copied:Atomics.load(task.state,sw.copied),successfulWords:task.successfulWords??0,waitingPolls:task.waitingPolls??0};}
function retainScene(){const task=scene.current;if(task&&!sceneTasks.includes(task))sceneTasks.push(task);}
function sceneCancel(){const task=scene.current;retainScene();if(task&&!sceneSnapshots.has(task))sceneSnapshots.set(task,sceneState(task));scene.cancel();}
function createWorker(url){
 const worker=new Worker(`const {parentPort,workerData}=require('node:worker_threads');
globalThis.self={postMessage:message=>parentPort.postMessage(message),close:()=>parentPort.close()};
import(workerData.url).then(()=>parentPort.on('message',data=>self.onmessage({data})));`,{eval:true,workerData:{url:url.href}});
 const terminal=new Promise(resolve=>worker.on('exit',code=>resolve(code)));threads.push(terminal);
 const facade={onmessage:null,onerror:null,terminal,
  postMessage:data=>worker.postMessage(data),terminate:()=>{const end=worker.terminate();terminations.push(end);return end;}};
 worker.on('message',data=>facade.onmessage?.({data}));worker.on('error',error=>facade.onerror?.({message:String(error)}));return facade;
}
const channel=new Th14StageRestoreDelivery({createWorker,onError:error=>errors.push(String(error))});
const scene=new Th14SharedSceneCopy({createWorker,onError:error=>errors.push(String(error))});
function schedule(action,delay){const token=setTimeout(()=>{timers.delete(token);try{action();}catch(error){errors.push(String(error));}},delay);timers.add(token);}
function retainTask(){
 const task=channel.current;if(!task||taskStates.includes(task))return;
 taskStates.push(task);
}
function taskState(task){return {generation:task.generation,operations:task.operations,
 ready:Atomics.load(task.state,w.ready),acknowledged:Atomics.load(task.state,w.ack),statusBeforeCleanup:Atomics.load(task.state,w.status)};}
function preserveBeforeCancel(){const task=channel.current;retainTask();if(task&&!taskSnapshots.has(task))taskSnapshots.set(task,taskState(task));}
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(wasmBytes,{env:{memory},wasi:{'thread-spawn':()=>{++cppThreadSpawns;throw new Error('Unexpected C++ thread spawn');}},wasi_snapshot_preview1:wasi.wasiImport,stagehost:{
 now_ms:()=>performance.now(),scene_prepare:()=>{const ok=scene.prepare();retainScene();return ok?1:0;},scene_cancel:sceneCancel,
 scene_read:(source,layout,index,offset,destination)=>{
  const map=Array.from(new Uint32Array(memory.buffer,layout,75));
  const status=scene.read(memory.buffer,source,map,index,offset);const task=scene.current;
  if(status===1){new Uint32Array(memory.buffer,destination,1)[0]=scene.value(index);task.successfulWords=(task.successfulWords??0)+1;}
  else if(status===0&&task)task.waitingPolls=(task.waitingPolls??0)+1;return status;
 },
 request_begin:(generation,playback)=>{
  schedule(()=>{
   if(!c.start_wait(generation))return;
   if(!channel.begin(playback!==0)){errors.push('Producer start failed');return;}
   retainTask();schedule(()=>c.finish_wait(generation),60);
  },0);return 1;
 },ready:operation=>channel.ready(operation),committed:operation=>channel.committed(operation)?1:0,
 cancel:()=>{preserveBeforeCancel();channel.cancel();}
}});
wasi.initialize(instance);c=instance.exports;
const meta=()=>Array.from({length:16},(_,index)=>c.meta(index)>>>0);
const text=pointer=>{const bytes=new Uint8Array(c.memory.buffer);let end=pointer;while(bytes[end])++end;return new TextDecoder().decode(bytes.subarray(pointer,end));};
const copy=bytes=>{const pointer=c.allocate(bytes.length);assert(pointer);new Uint8Array(c.memory.buffer,pointer,bytes.length).set(bytes);return pointer;};
// Archive::open borrows its source. Match Application's archive owner lifetime;
// freeing this block after parsing the directory corrupts later resource reads.
const archivePointer=copy(archive);assert.equal(c.open_archive(archivePointer,archive.length),1,text(c.error()));
if(entry==='direct'){
 const pointer=copy(replay);
 assert.equal(c.begin_replay(pointer,replay.length,initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0x1aec84),1,text(c.error()));
 c.release(pointer);
}else{
 const enter=entry==='queued-loading-title'?c.probe_queued_loading_entry:c.probe_loading_entry;
 assert.equal(enter(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0x1aec84),1,text(c.error()));
}
started=true;
const stageFrames=Array.from({length:7},(_,index)=>c.stage_frames(index+1)>>>0);
const bindings={buildSha256:sha(buildRaw),browserBuildSha256:sha(browserRaw),assetManifestSha256:sha(manifestRaw),
 replaySha256:sha(replay),archiveSha256:sha(archive),nativeReportSha256:sha(nativeReportRaw),
 nativeSelectedSha256:sha(expected),initialProfileSha256:sha(initialRaw),toolSha256:sha(readFileSync(import.meta.filename))};
put('plan.json',{pid:process.pid,argv:process.argv,bindings,stageFrames,nativeCallbacks:nativeReport.callbacks,
 originalInputsUsedOnlyOnce:['initial monotonic tick integer','security cookie','declared geometry frame'],
 entry,directReplayEntry:entry==='direct',declaredCpuReadyLoadingPrelude:entry!=='direct',
 bootstrapTextureChunksQueued:entry==='queued-loading-title',
 coldNativeBootstrapReproduced:false,realTimeCadence:cadenceMode==='real',cadenceMode,maximumCallbacks,sharedWasmMemory:true,workerDirectlyReadsLiveCamera:true,bootstrapRealTimeCadence:false,
 callbackVmOrRecordSpecificReadyTargets:false,originalObservationValuesWrittenToEngine:false,
 gpuAndAudioAcceptance:false,completeGame:false});
const began=performance.now();let previous=began;
function collect(){
 const words=c.rows_words()>>>0;assert.equal(words%114,0);
 const data=new Uint32Array(c.memory.buffer,c.rows_data(),words);
 const fresh=words&&data[0]===observed+1;
 assert(!words||fresh||data[words-114]===observed,'Uncollected observation gap');
 if(fresh)writeSync(fd,Buffer.from(data.buffer,data.byteOffset,data.byteLength));
 for(let at=0;fresh&&at<words;at+=114){
  assert.equal(data[at],++observed);const stage=data[at+31];stageCounts[stage]=(stageCounts[stage]??0)+1;
  if(stage!==lastStage){stageEntries.push({stage,callback:observed,elapsedSeconds:(performance.now()-began)/1000});lastStage=stage;}
  if(observed<=nativeReport.callbacks){
   const n=observed-1,different=[];
   for(let field=0;field<32;++field)if(data[at+1+field]!==expected.readUInt32LE(n*128+field*4)){
    counts[field]=(counts[field]??0)+1;different.push(field);
   }
   if(different.length){const item={callback:observed,stage,fields:different};firstDifference??=item;firstByStage[stage]??=item;}
   for(let field=0;field<75;++field){const value=field<73?originalCamera.readUInt32LE(n*292+field*4):cameraTail.readUInt32LE(n*8+(field-73)*4);
    if(data[at+33+field]!==value)cameraCounts[field]=(cameraCounts[field]??0)+1;
   }
   for(let field=0;field<2;++field)if(data[at+108+field]!==originalHud.readUInt32LE(n*8+field*4))hudCounts[field]=(hudCounts[field]??0)+1;
   ++compared;
  }
 }
 const total=c.events_words()>>>0;assert.equal(total%12,0);
 if(total>lastEvents){const array=new Uint32Array(c.memory.buffer,c.events_data(),total);
  const file=openSync(resolve(out,'delivery-events.u32'),lastEvents?'a':'wx');
  writeSync(file,Buffer.from(array.buffer,array.byteOffset+lastEvents*4,(total-lastEvents)*4));closeSync(file);lastEvents=total;
 }
}
function progress(terminal=false){
 finalMeta=meta();const elapsed=(performance.now()-began)/1000;
 const fs=statfsSync(root,{bigint:true});assert(fs.bavail*fs.bsize>=100n*1024n**3n,'Preserve 100 GiB free');
 const record={pid:process.pid,terminal,elapsedSeconds:elapsed,displayFrames,callbacks:observed,stage:finalMeta[1],phase:finalMeta[0],
  nativeComparedCallbacks:compared,differenceFieldCount:Object.keys(counts).length,firstDifference,
  stageCounts,stageEntries,workerTasks:taskStates.length,errors:errors.length,
  completeGame:false,nativeEquivalent:false,rawOutputBytes:observed*114*4};
 put('progress.json',record);console.log(JSON.stringify({elapsedSeconds:Math.round(elapsed),callbacks:observed,stage:finalMeta[1],
  producerTasks:taskStates.length,nativeDifferenceFields:Object.keys(counts).length,terminal}));
}
try{
 collect();
 while(true){
  const now=performance.now(),seconds=(now-previous)/1000;previous=now;
  if(!c.frame(cadenceMode==='real'?seconds:1/60)){stoppedBy='engine-failure';errors.push(text(c.error()));break;}
  ++displayFrames;collect();const state=meta();
  if(errors.length){stoppedBy='host-failure';break;}
  if(state[0]===4){stoppedBy=state[5]?'game-over':'session-finished';break;}
  if(state[11]||state[12]){stoppedBy='unsupported-bullet-operation';break;}
  if(now-began>=maximumSeconds*1000){stoppedBy='declared-wall-limit';break;}
  if(observed>=maximumCallbacks){stoppedBy='declared-callback-limit';break;}
  if(now-lastProgress>=20000){progress();lastProgress=now;}
  // The real FrameCadence owns retained debt and the bounded four-tick catchup.
  // This timer supplies display opportunities, never a game/VM readiness target.
  await new Promise(resolve=>setTimeout(resolve,cadenceMode==='fast'?0:Math.max(1,1000/60-(performance.now()-now))));
 }
}catch(error){exception=String(error?.stack??error);stoppedBy='exception';}
finally{
 try{collect();}catch(error){exception??=String(error);}
 // Give a fully acknowledged producer its own normal terminal opportunity.
 if(channel.current&&Atomics.load(channel.current.state,w.ack)===channel.current.operations){
  let watchdog;try{await Promise.race([channel.current.worker.terminal,new Promise(resolve=>{watchdog=setTimeout(resolve,1000);})]);}
  finally{clearTimeout(watchdog);}
 }
 for(const task of taskStates)completedTasks.push(taskSnapshots.get(task)??taskState(task));
 progress(true);for(const token of timers)clearTimeout(token);timers.clear();
 if(started)c.close_session();sceneCancel();channel.cancel();c.release(archivePointer);closeSync(fd);
 await Promise.all(terminations);await Promise.all(threads);
}
const strictPrefixPassed=compared===nativeReport.callbacks&&Object.keys(counts).length===0&&Object.keys(cameraCounts).length===0&&Object.keys(hudCounts).length===0;
const report={schema:'th14/independent-full-session-run/1',terminal:true,pid:process.pid,stoppedBy,exception,
 actualGameSessionRun:true,entry,directReplayEntry:entry==='direct',declaredCpuReadyLoadingPrelude:entry!=='direct',
 coldNativeBootstrapReproduced:false,all141CurrentGameUnitsFromFreshFrozenBuild:true,
 gameObjectsReusedForThisFixtureLink:entry==='direct'?0:141,realFrameCadenceAndClock:cadenceMode==='real',cadenceMode,sharedWasmMemory:true,callbacks:observed,displayFrames,
 elapsedSeconds:(performance.now()-began)/1000,stageFrames,stageCounts,stageEntries,end:finalMeta,
 nativeComparedCallbacks:compared,nativeCapturedCallbacks:nativeReport.callbacks,
 strictOriginalPrefixPassed:strictPrefixPassed,differenceCounts:counts,firstDifference,firstByStage,
 camera75DifferenceCounts:cameraCounts,hudDifferenceCounts:hudCounts,deliveryEvents:lastEvents/12,
 producerTasks:completedTasks,sceneTasks:sceneTasks.map(task=>sceneSnapshots.get(task)??sceneState(task)),cppThreadSpawns,workerThreadsTerminal:threads.length,errors,bindings,
 observedNativeReadyFrameVmTargetsUsed:false,originalObservationValuesWrittenToEngine:false,
 gpuOrAudioDeviceExecuted:false,ordinaryBrowserAccepted:false,originalSchedulingAccepted:false,workerDirectlyReadsActualCamera:true,perCameraWordAcknowledgements:false,
 extraAckSynchronizationCostUncalibrated:true,wholeReplayAcceptance:false,completeGame:false,nativeEquivalent:false,
 observationStrideWords:114,observationsSha256:sha(read(rawPath))};
put('report.json',report);
console.log(JSON.stringify({terminal:true,stoppedBy,callbacks:observed,stages:stageEntries.map(row=>row.stage),
 producerTasks:taskStates.length,strictOriginalPrefixPassed:strictPrefixPassed,wholeReplayAcceptance:false}));
process.exitCode=exception||errors.length?3:strictPrefixPassed?0:2;
