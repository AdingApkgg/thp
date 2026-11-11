import { isTh14ForcedReplayMenu } from './th14-replay-end-predicate-nov08.mjs';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,statfsSync,existsSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationGlesPlatform} from './th14-full-application-gles-transition-type0-nov09.mjs';
const root=resolve(import.meta.dirname,'..'),opts=new Map();
for(let i=2;i<process.argv.length;i+=2){assert(process.argv[i].startsWith('--')&&process.argv[i+1]);opts.set(process.argv[i].slice(2),process.argv[i+1]);}
const home=resolve(root,'artifacts/th14/current-low-pause-transition-nov12');
const out=resolve(home,opts.get('output')??'cpp-pair'),rel=relative(home,out);assert(rel&&!rel.startsWith('..')&&!isAbsolute(rel));
const maximumCallbacks=Number(opts.get('callbacks')??16400),maximumSeconds=Number(opts.get('seconds')??600),maximumFrames=Number(opts.get('frames')??20000);
assert.equal(opts.get('mode'),'candidate');
assert(maximumCallbacks>0&&maximumCallbacks<=150000&&maximumSeconds>=1&&maximumSeconds<=3000&&maximumFrames>0&&maximumFrames<=180000);
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const component=resolve(root,'artifacts/th14/current-low-pause-transition-nov12/component'),buildRaw=read(resolve(component,'build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(component,opts.get('mode')+'.wasm'));
assert(build.compiled&&build.actualColdApplicationInitializeTickAndDraw&&build.noDeclaredPerFileReadinessSchedule);
assert.equal(sha(wasm),build.wasmSha256);assert.equal(sha(read(resolve(component,'fixture.cpp'))),build.fixtureSha256);
for(const [path,digest]of Object.entries(build.sourceBindingsByMode[opts.get('mode')]))assert.equal(sha(read(resolve(root,path))),digest);
const native=resolve(root,opts.get('native')??'artifacts/th14/low-pause-input-key-native-nov09/input-key-prefix'),nativeRelative=relative(resolve(root,'artifacts/th14'),native);
assert(nativeRelative&&!nativeRelative.startsWith('..')&&!isAbsolute(nativeRelative));
const initialRaw=read(resolve(native,'untouched-first-player.json')),initial=JSON.parse(initialRaw),nativePlanRaw=read(resolve(home,'native-reference-metadata.json')),nativePlan=JSON.parse(nativePlanRaw);
assert(nativePlan.originalCallbacks===35000&&nativePlan.nativeCaptureTerminal&&nativePlan.reportedDebugErrors===0);
const nativeReceipt=load(resolve(home,'native-terminal-receipt.json'));
assert(nativeReceipt.reaped&&nativeReceipt.exitCode===0&&nativeReceipt.childExited);
assert.equal(sha(read(resolve(home,'native-terminal-receipt.json'))),nativePlan.terminalReceiptSha256);
assert(nativePlan.noDebuggerAttached&&nativePlan.afterResumeThreadSuspensions===0);

assert.equal(nativePlan.nativePath,relative(root,native).replaceAll('\\','/'));
assert.equal(sha(initialRaw),nativePlan.initialSha256);
assert.deepEqual(initial.words.slice(27,31),[0,1,1,1]);
assert.equal(sha(read(resolve(native,'untouched-first-player.json'))),sha(initialRaw),'Native one-time profile changed');
assert.equal(initial.attractFlags&~0x40,nativePlan.caseInitialization.afterFlags);
// Reference rows intentionally remain unread until both processes terminate.
const assets=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),manifest=load(resolve(assets,'manifest.json'));
assert(manifest.passed&&manifest.unchangedEntries===226);assert.equal(sha(read(resolve(assets,'th14.dat'))),manifest.referenceArchiveSha256);
const runtime=resolve(root,'artifacts/th14/stable-stage-close-nov07/runtime-ready');
assert(statfsSync(root,{bigint:true}).bavail*statfsSync(root,{bigint:true}).bsize>=100n*1024n**3n);
const prerequisite=load(resolve(root,'artifacts/th14/current-marisaa-hard-focused-nov08/qualified.json'));
assert(prerequisite.qualifiedOwnedTerminalPair&&prerequisite.allChildrenWorkersHostsGpuAndClockRetired,'Retire and audit the current Hard pair before starting another game');
for(const [path,digest]of Object.entries(build.objectBindings))assert.equal(sha(read(resolve(root,path))),digest);
assert(load(resolve(root,'artifacts/th14/reimub-shot-coverage-nov08/qualified-input-key-v3-nov09.json')).allWorkersHostsGpuAndClockRetired);
assert.equal(build.snapshotLimit,128);assert.equal(build.targetInputKeys.length,123);
const previous=load(resolve(root,'artifacts/th14/reimub-shot-coverage-nov08/qualified-rng-origin-v4-nov09.json'));assert(previous.qualifiedOwnedCurrentPrefix&&previous.allWorkersHostsGpuAndClockRetired,'Previous expanded run must be retired and audited');
mkdirSync(out);mkdirSync(resolve(out,'save'));mkdirSync(resolve(out,'save/replay'));
copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(out,'save/th14.cfg'));
const put=(file,value)=>writeFileSync(resolve(out,file),JSON.stringify(value,null,2)+'\n');
for(const file of [import.meta.filename,resolve(root,'tools/th14-full-application-gles-transition-type0-nov09.mjs')])copyFileSync(file,resolve(out,file.split(/[\\/]/).at(-1)));
const module=await WebAssembly.compile(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationGlesPlatform(module,memory,{clockInput:initial.actualInitialTimeGetTimeInput,archivePath:resolve(assets,'th14.dat'),fontDirectory:resolve(runtime,'fonts'),saveDirectory:resolve(out,'save'),angleDirectory:'C:/Users/APKGG/AppData/Local/Programs/Trae',onAsyncError:e=>errors.push(String(e?.stack??e))});
platform.env.th14_async_schedule_impl=(callback,data,delay)=>{
 assert(callback>0&&delay>=0&&delay<=60000);
 const token=setTimeout(()=>{platform.timers.delete(token);try{c.async_deliver_owned(callback,data);}catch(e){errors.push(String(e?.stack??e));}},delay);platform.timers.add(token);
};
const ioTimes=[],ioNames=new Map();
const ioString=p=>{const b=new Uint8Array(memory.buffer,p,Math.min(4096,memory.buffer.byteLength-p));const end=b.indexOf(0);assert(end>=0);return new TextDecoder().decode(b.subarray(0,end));};
for(const name of ['SDL_IOFromFile','SDL_WriteIO','SDL_CloseIO']){
 const original=platform.env[name];assert.equal(typeof original,'function');platform.env[name]=(...args)=>{
  const path=name==='SDL_IOFromFile'?ioString(args[0]):ioNames.get(args[0])??null,entered=process.hrtime.bigint();
  const result=original(...args),ended=process.hrtime.bigint();
  if(name==='SDL_IOFromFile'&&result)ioNames.set(result,path);if(name==='SDL_CloseIO')ioNames.delete(args[0]);
  ioTimes.push({name,path,enteredNs:entered.toString(),endedNs:ended.toString(),durationNs:Number(ended-entered),requestedBytes:name==='SDL_WriteIO'?args[2]:null,result});return result;
 };
}
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>{errors.push(String(e));put('worker-fatal.json',{error:String(e),completeGame:false});process.exit(3);}}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(out,'save'),'/music':resolve(runtime,'music')}});
const instance=await WebAssembly.instantiate(module,{observerhost:{now_ns:()=>process.hrtime.bigint()},env:platform.env,wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool,'No prepared full Application worker available');return pool.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const state=()=>Array.from(new Uint32Array(memory.buffer,c.state(),16)),error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
const states=[],frameTimes=[],differences={},cameraDifferences={},hudDifferences={},shotIndex=[];let frames=0,observed=0,captured=0,exception=null,stoppedBy='unknown',firstRow=null,lastState=null,created=false,closed=false;
const began=performance.now();
put('plan.json',{pid:process.pid,nativePath:relative(root,native).replaceAll('\\','/'),wasmSha256:sha(wasm),buildSha256:sha(buildRaw),initialSha256:sha(initialRaw),comparisonPending:true,nativeObserverPlanSha256:sha(nativePlanRaw),nativeReportSha256:null,replaySha256:manifest.replaySha256,archiveSha256:manifest.referenceArchiveSha256,callbacks:maximumCallbacks,maximumSeconds,maximumFrames,actualApplication:true,graphicsServicesDeclared:true,hostOpportunityPollRequestedMs:1,actualCppFrameCadence:true,noPerFileReadinessSchedule:true,noRngOrCounterPadding:true,hardwarePixels:false,completeGame:false});
function collect(){
 const count=c.observation_count()>>>0,words=c.observation_words()>>>0;assert.equal(words,count*114);assert(count>=observed);
 const rows=new Uint32Array(memory.buffer,c.observation_data(),words);
 for(let i=observed;i<count;i++){
  assert.equal(rows[i*114],i+1);const row=rows.subarray(i*114,(i+1)*114);firstRow??=Array.from(row);
  // Immutable raw C++ observation only; no online reference accesses.
 }
 observed=count;const total=c.shot_snapshot_count()>>>0;assert(total>=captured&&total<=build.snapshotLimit);
 const stride=4+256*96,shots=new Uint32Array(memory.buffer,c.shot_snapshot_data(),total*stride);
 for(let i=captured;i<total;i++){const at=i*stride,head=shots.subarray(at,at+4),data=Buffer.from(shots.buffer,shots.byteOffset+(at+4)*4,256*96*4),file='shot-'+head[0]+'.u32';writeFileSync(resolve(out,file),data,{flag:'wx'});shotIndex.push({callback:head[0],stage:head[1],stageFrame:head[2],inputKey:[rows[(head[0]-1)*114+31],rows[(head[0]-1)*114+112],rows[(head[0]-1)*114+110],rows[(head[0]-1)*114+111]],stride:96,slots:256,file,bytes:data.length,sha256:sha(data)});}
 captured=total;
}
try{
 assert.equal(c.shot_snapshot_enable(1),1);created=true;assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,1),1,error());
 let previousOpportunity=-1,lastProgress=0,lastCallbackCount=0,lastCallbackAt=began,lastTerminalSample=0;const terminalSamples=[];
 while(frames<maximumFrames&&observed<maximumCallbacks&&performance.now()-began<maximumSeconds*1000){
  if(existsSync(resolve(home,'owner-stop-request.json'))){stoppedBy='declared-owner-stop';break;}
  const now=performance.now(),delta=previousOpportunity<0?0:(now-previousOpportunity)/1000;previousOpportunity=now;
  const beforeTicks=c.frame_tick_count()>>>0,ok=c.frame(delta),after=performance.now();frames=c.frame_tick_count()>>>0;
  if(frames>beforeTicks){assert.equal(platform.getError(),0,'GPU frame '+frames);
   frameTimes.push([frames,now-began,after-now,delta*1000]);collect();
   const current=state();if(!lastState||current.some((v,i)=>v!==lastState[i]))states.push({frame:frames,ms:after-began,words:current});lastState=current;
  }
  const current=lastState??state();
  if(observed!==lastCallbackCount){lastCallbackCount=observed;lastCallbackAt=after;}
  const end=Array.from(new Uint32Array(memory.buffer,c.campaign_end_state(),18));
  const atForcedMenu=isTh14ForcedReplayMenu(end);
  if(atForcedMenu&&after-lastTerminalSample>=1000){lastTerminalSample=after;terminalSamples.push({ms:after-began,callbacks:observed,words:end});}
  if(atForcedMenu&&terminalSamples.length>=3&&after-lastCallbackAt>=3000){stoppedBy='campaign-forced-replay-menu-stable';put('campaign-terminal.json',{samples:terminalSamples,quietSinceLastCallbackMs:after-lastCallbackAt,readOnly:true,completeGame:false});break;}
  if(!ok){stoppedBy='Application-failure';throw Error(error());}assert.equal(errors.length,0,errors.join('\n'));
  if(after-lastProgress>10000){lastProgress=after;put('progress.json',{pid:process.pid,frames,callbacks:observed,state:current,elapsedSeconds:(after-began)/1000});console.log(JSON.stringify({frames,callbacks:observed,scriptCalls:current[2],stage:current[10],phase:current[9]}));}
  await new Promise(r=>setTimeout(r,1));
 }
 if(stoppedBy==='unknown')stoppedBy=observed>=maximumCallbacks?'declared-callback-limit':frames>=maximumFrames?'declared-frame-limit':'declared-wall-limit';
}catch(e){exception=String(e?.stack??e);if(stoppedBy==='unknown')stoppedBy='exception';}
finally{
 try{if(created){collect();lastState=state();const n=c.observation_words()>>>0;writeFileSync(resolve(out,'observations.u32'),Buffer.from(new Uint32Array(memory.buffer,c.observation_data(),n).slice().buffer));c.close();closed=true;
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0,'Async callbacks must retire before instance release');}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));clock.close();
 try{put('platform-before-gpu-close.json',platform.summary());assert.equal(platform.getError(),0,'GPU teardown');platform.closeGpu();}catch(e){exception??=String(e?.stack??e);}
}
const expandedWords=c.expanded_shot_vm_size()>>>0;assert.equal(expandedWords%307,0);
const expandedShotBytes=Buffer.from(new Uint32Array(memory.buffer,c.expanded_shot_vm_data(),expandedWords).slice().buffer);
writeFileSync(resolve(out,'expanded-shot-vms.u32'),expandedShotBytes,{flag:'wx'});
const fullWords=c.full_vm_checkpoint_size()>>>0;
const fullVmBytes=Buffer.from(new Uint32Array(memory.buffer,c.full_vm_checkpoint_data(),fullWords).slice().buffer);
writeFileSync(resolve(out,'full-vm-checkpoints.u32'),fullVmBytes,{flag:'wx'});
const fullRows=new Uint32Array(fullVmBytes.buffer,fullVmBytes.byteOffset,fullVmBytes.length/4),fullSnapshots=[];
for(let offset=0;offset<fullRows.length;){
 assert(offset+7<=fullRows.length);const h=Array.from(fullRows.subarray(offset,offset+7));offset+=7;
 assert(h[0]>=1&&h[0]<=observed&&h[3]<=8192&&h[6]===303);
 assert(offset+h[3]*303<=fullRows.length);
 fullSnapshots.push({callback:h[0],stage:h[1],stageFrame:h[2],count:h[3],complete:h[4]===1,expected:h[5],stride:h[6]});offset+=h[3]*303;
}
assert.equal(new Set(fullSnapshots.map(s=>s.callback)).size,fullSnapshots.length);
assert(fullSnapshots.every((s,i)=>i===0||s.callback>fullSnapshots[i-1].callback));
const ownObservationBytes=read(resolve(out,'observations.u32'));
const ownRows=new Uint32Array(ownObservationBytes.buffer,ownObservationBytes.byteOffset,ownObservationBytes.length/4);
const actualKey=callback=>{const p=(callback-1)*114;assert(p>=0&&p+114<=ownRows.length);return [ownRows[p+31],ownRows[p+112],ownRows[p+110],ownRows[p+111]];};
for(const snapshot of fullSnapshots){snapshot.inputKey=actualKey(snapshot.callback);assert(build.fullVmTargetKeys.some(key=>key.every((v,i)=>v===snapshot.inputKey[i])));}
const keyText=key=>key.join(','),actualShotKeys=shotIndex.map(s=>keyText(s.inputKey)),declaredKeys=build.targetInputKeys.filter(k=>k[0]===1||(k[0]===2&&k[2]<=2146)).map(keyText);
const declaredSet=new Set(declaredKeys),actualSet=new Set(actualShotKeys);
const keyCoverage={declared:declaredKeys.length,observed:actualShotKeys.length,missing:declaredKeys.filter(k=>!actualSet.has(k)),unexpected:actualShotKeys.filter(k=>!declaredSet.has(k)),duplicates:actualShotKeys.length-actualSet.size};
keyCoverage.complete=keyCoverage.missing.length===0&&keyCoverage.unexpected.length===0&&keyCoverage.duplicates===0&&keyCoverage.observed===declaredKeys.length;
put('input-key-sampling.json',{...keyCoverage,fullVmSamples:fullSnapshots,actualCppCallbacksPreserved:true,noGlobalCallbackOffsetApplied:true,noDesiredStateValuesUsed:true,completeGame:false});
put('expanded-vm-report.json',{readOnly:true,shotVmRows:expandedWords/307,shotVmStride:307,shotVmSha256:sha(expandedShotBytes),fullSnapshots,fullVmSha256:sha(fullVmBytes),rawIdentitiesAndRegistryOrderRetained:true,noReferenceVmSupplied:true,completeGame:false});
const originCount=c.origin_rng_count()>>>0;assert(originCount<=65536);
const originBytes=Buffer.from(new Uint32Array(memory.buffer,c.origin_rng_data(),originCount*24).slice().buffer);
writeFileSync(resolve(out,'origin-rng-events.u32'),originBytes,{flag:'wx'});
put('origin-rng-report.json',{rows:originCount,stride:24,sha256:sha(originBytes),mainThreadOnly:true,
 filesAndScripts:[[2,16],[9,6],[9,8]],boundaryPoints:['BeforeRead','SeedWritten'],
 globalSnapshotNotInstructionRegisterValue:true,readOnly:true,mayAffectScheduling:true,completeGame:false});
const rngTraceCount=c.observer_rng_count()>>>0,mainTraceCount=c.observer_main_count()>>>0;
assert(rngTraceCount<=256&&mainTraceCount===observed);
const rngTraceBytes=Buffer.from(new Uint32Array(memory.buffer,c.observer_rng_data(),rngTraceCount*16).slice().buffer);
const mainTraceBytes=Buffer.from(new Uint32Array(memory.buffer,c.observer_main_data(),mainTraceCount*8).slice().buffer);
writeFileSync(resolve(out,'rng-store-events.u32'),rngTraceBytes,{flag:'wx'});writeFileSync(resolve(out,'main-observer-times.u32'),mainTraceBytes,{flag:'wx'});
put('trace-report.json',{rngTraceCount,mainTraceCount,rngTraceSha256:sha(rngTraceBytes),mainTraceSha256:sha(mainTraceBytes),postStoreClockObserverDeclared:true,postStoreEventsActuallyObserved:rngTraceCount>0,readOnly:true,noTargets:true,completeGame:false});
const frameWords=c.frame_trace_words()>>>0;assert.equal(frameWords%14,0);
const frameBytes=Buffer.from(new Uint32Array(memory.buffer,c.frame_trace_data(),frameWords).slice().buffer);
writeFileSync(resolve(out,'actual-frame-dispatch.u32'),frameBytes,{flag:'wx'});
put('actual-frame-report.json',{opportunities:c.frame_opportunity_count()>>>0,ticks:c.frame_tick_count()>>>0,traceRows:frameWords/14,traceSha256:sha(frameBytes),actualCppFrameCadence:true,repeatUpdateLoop:true,rendererDeferCommit:true,noManualNodeDeadline:true,completeGame:false});
put('sdl-file-times.json',ioTimes);
const codecWarmCount=c.codec_warm_count()>>>0;assert.equal(codecWarmCount,0);
const codecWarmBytes=Buffer.from(new Uint32Array(memory.buffer,c.codec_warm_data(),codecWarmCount*12).slice().buffer);
writeFileSync(resolve(out,'codec-warm-state.u32'),codecWarmBytes,{flag:'wx'});
put('codec-warm-report.json',{count:codecWarmCount,sha256:sha(codecWarmBytes),candidateOnly:true,completeGame:false});
put('shot-index.json',{readOnly:true,originalValuesSuppliedToEngine:false,snapshots:shotIndex});put('application-states.json',{stateWords:['signatureDraws','asciiHandle','scriptCalls','scriptSeed','bootUploadIndex','signatureActive','bootWorker','titleWorker','audioWorker','phase','stage','frame','keepalive','pushes','pops','callbacks'],states});put('frame-times.json',frameTimes);
const platformSummary=platform.summary();put('platform.json',platformSummary);
const captureComplete=stoppedBy==='declared-callback-limit'&&observed>=maximumCallbacks&&captured===declaredKeys.length&&keyCoverage.complete&&fullSnapshots.length===2&&fullSnapshots.every(s=>s.complete)&&!exception&&!errors.length;
const strict=false; // Cannot accept equivalence before the offline audit.
const report={schema:'th14/current-low-pause-transition-prefix/1',referenceRowsReadDuringExecution:false,stableForcedReplayMenuObserved:stoppedBy==='campaign-forced-replay-menu-stable',terminal:true,pid:process.pid,stoppedBy,exception,errors,closed,frames,callbacks:observed,shotSnapshots:captured,expandedShotVmRows:expandedWords/307,fullVmSnapshots:fullSnapshots.length,elapsedSeconds:(performance.now()-began)/1000,firstRow,lastState,selectedDifferences:differences,cameraDifferences,hudDifferences,strictBoundedStatePassed:strict,comparisonPending:true,onlineReferenceCompared:false,comparedCallbacks:0,captureComplete,workers:pools.flatMap(p=>p.summary()),physicalWorkers:pools.flatMap(p=>p.physicalSummary()),processClockResolution:clock.state,actualColdApplicationInitializeTickAndDraw:true,actualAudioMixerSilentQueue:true,graphicsRecordingOnly:false,actualNativeGles:true,noDeclaredPerFileReadinessSchedule:true,productionCodeChanged:false,allModesOrFullReplayAccepted:false,hardwarePixelsAccepted:false,audioEquivalent:false,completeGame:false,wasmSha256:sha(wasm),driverSha256:sha(read(import.meta.filename)),platformSha256:sha(read(resolve(root,'tools/th14-full-application-gles-transition-type0-nov09.mjs')))};
put('report.json',report);console.log(JSON.stringify({stoppedBy,callbacks:observed,frames,exception,selectedDifferences:differences,cameraDifferences,hudDifferences,strict}));if(!captureComplete)process.exitCode=1;
