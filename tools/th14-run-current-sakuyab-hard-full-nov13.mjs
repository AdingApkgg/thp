import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,statfsSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const root=resolve(import.meta.dirname,'..'),opts=new Map();
for(let i=2;i<process.argv.length;i+=2){assert(process.argv[i].startsWith('--')&&process.argv[i+1]);opts.set(process.argv[i].slice(2),process.argv[i+1]);}
const home=resolve(root,'artifacts/th14/current-sakuyab-hard-full-nov13');
const out=resolve(home,opts.get('output')??'full-campaign'),rel=relative(home,out);assert(rel&&!rel.startsWith('..')&&!isAbsolute(rel));
const maximumCallbacks=Number(opts.get('callbacks')??12500),maximumSeconds=Number(opts.get('seconds')??360),maximumFrames=Number(opts.get('frames')??24000);
assert(['parent','candidate'].includes(opts.get('mode')));
assert(maximumCallbacks>0&&maximumCallbacks<=150000&&maximumSeconds>=1&&maximumSeconds<=3000&&maximumFrames>0&&maximumFrames<=180000);
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const component=resolve(root,'artifacts/th14/native-viewer-application-nov13/component-v4'),buildRaw=read(resolve(component,'build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(component,opts.get('mode')+'.wasm'));
assert(build.compiled&&build.actualColdApplicationInitializeTickAndDraw&&build.noDeclaredPerFileReadinessSchedule);
assert.equal(sha(wasm),build.outputs[opts.get('mode')].wasmSha256);assert.equal(sha(read(resolve(component,'fixture.cpp'))),build.fixtureSha256);
for(const [path,digest]of Object.entries(build.sourceBindingsByMode[opts.get('mode')]))assert.equal(sha(read(resolve(root,path))),digest);
const native=resolve(root,opts.get('native')??'artifacts/th14/player-entry-end-menu-nov06/campaign'),nativeRelative=relative(resolve(root,'artifacts/th14'),native);
assert(nativeRelative&&!nativeRelative.startsWith('..')&&!isAbsolute(nativeRelative));
const initialRaw=read(resolve(native,'untouched-first-player.json')),initial=JSON.parse(initialRaw),nativePlanRaw=read(resolve(native,'plan.json')),nativePlan=JSON.parse(nativePlanRaw);
assert(nativePlan.maximumCallbacks===150000&&nativePlan.textOnlyChangeVerifiedBeforeResume&&!nativePlan.bootDrawCounterLogger&&nativePlan.stopAfterStableForcedReplayEndMenu);
assert.deepEqual(initial.words.slice(27,31),[0,1,1,1]);
assert.equal(sha(read(resolve(native,'untouched-first-player.json'))),sha(initialRaw),'Native one-time profile changed');
assert.equal(initial.attractFlags&~0x40,initial.caseFlagsAfter);
// Reference rows intentionally remain unread until both processes terminate.
const assets=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-866bf6bac02e'),manifest=load(resolve(assets,'manifest.json'));
assert(manifest.passed&&manifest.unchangedEntries===226);assert.equal(sha(read(resolve(assets,'th14.dat'))),manifest.referenceArchiveSha256);
const runtime=resolve(root,'artifacts/th14/stable-stage-close-nov07/runtime-ready');
const music=load(resolve(root,'artifacts/th14/published-vorbis-cache-nov13/prepared.json'));assert(music.passed&&music.tracks===18);const musicDirectory=resolve(root,music.musicDirectory);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(read(resolve(musicDirectory,n))),h,n);
assert(statfsSync(root,{bigint:true}).bavail*statfsSync(root,{bigint:true}).bsize>=100n*1024n**3n);
mkdirSync(out);mkdirSync(resolve(out,'save'));mkdirSync(resolve(out,'save/replay'));
copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(out,'save/th14.cfg'));
const put=(file,value)=>writeFileSync(resolve(out,file),JSON.stringify(value,null,2)+'\n');
for(const file of [import.meta.filename,resolve(root,'tools/th14-full-application-recording-platform-uniform2-nov13.mjs')])copyFileSync(file,resolve(out,file.split(/[\\/]/).at(-1)));
const module=await WebAssembly.compile(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:initial.actualInitialTimeGetTimeInput,archivePath:resolve(assets,'th14.dat'),fontDirectory:resolve(runtime,'fonts'),saveDirectory:resolve(out,'save'),onAsyncError:e=>errors.push(String(e?.stack??e))});
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
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(out,'save'),'/music':musicDirectory}});
const instance=await WebAssembly.instantiate(module,{observerhost:{now_ns:()=>process.hrtime.bigint()},env:platform.env,wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool,'No prepared full Application worker available');return pool.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const state=()=>Array.from(new Uint32Array(memory.buffer,c.state(),16)),error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
const states=[],frameTimes=[],differences={},cameraDifferences={},hudDifferences={},shotIndex=[];let frames=0,observed=0,captured=0,exception=null,stoppedBy='unknown',firstRow=null,lastState=null,created=false,closed=false;
const began=performance.now();
put('plan.json',{pid:process.pid,nativePath:relative(root,native).replaceAll('\\','/'),wasmSha256:sha(wasm),buildSha256:sha(buildRaw),initialSha256:sha(initialRaw),comparisonPending:true,targetSelection:[2,1,2],startupClockProfileFromNormalCase:true,nativeObserverPlanSha256:sha(nativePlanRaw),nativeReportSha256:null,replaySha256:manifest.replaySha256,archiveSha256:manifest.referenceArchiveSha256,callbacks:maximumCallbacks,maximumSeconds,maximumFrames,actualApplication:true,graphicsServicesDeclared:true,hostOpportunityPollRequestedMs:1,actualCppFrameCadence:true,noPerFileReadinessSchedule:true,noRngOrCounterPadding:true,hardwarePixels:false,completeGame:false});
function collect(){
 const count=c.observation_count()>>>0,words=c.observation_words()>>>0;assert.equal(words,count*114);assert(count>=observed);
 const rows=new Uint32Array(memory.buffer,c.observation_data(),words);
 for(let i=observed;i<count;i++){
  assert.equal(rows[i*114],i+1);const row=rows.subarray(i*114,(i+1)*114);assert.deepEqual(Array.from(row.subarray(28,31)),[2,1,2]);firstRow??=Array.from(row);
  // Immutable raw C++ observation only; no online reference accesses.
 }
 observed=count;const total=c.shot_snapshot_count()>>>0;assert(total>=captured&&total<=80);
 const stride=4+256*96,shots=new Uint32Array(memory.buffer,c.shot_snapshot_data(),total*stride);
 for(let i=captured;i<total;i++){const at=i*stride,head=shots.subarray(at,at+4),data=Buffer.from(shots.buffer,shots.byteOffset+(at+4)*4,256*96*4),file='shot-'+head[0]+'.u32';writeFileSync(resolve(out,file),data,{flag:'wx'});shotIndex.push({callback:head[0],stage:head[1],stageFrame:head[2],stride:96,slots:256,file,bytes:data.length,sha256:sha(data)});}
 captured=total;
}
try{
 assert.equal(c.shot_snapshot_enable(0),1);created=true;assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 // Cold real Application initialization, followed by the hosted replay API.
 // The startup clock/cookie profile is declared, not the Hard target state.
 const until=performance.now()+60000;let prior=-1;
 while(!c.viewer_ready()){
  assert(performance.now()<until,'cold replay open readiness timeout');const now=performance.now();
  assert(c.frame(prior<0?0:(now-prior)/1000),error());prior=now;await new Promise(r=>setTimeout(r,1));
 }
 assert.equal(c.observation_count(),0,'No demo callbacks may precede the selected Hard case');
 const payload=read(manifest.replayPath);assert.equal(sha(payload),manifest.replaySha256);
 const pointer=c.viewer_alloc(payload.length);assert(pointer);try{new Uint8Array(memory.buffer,pointer,payload.length).set(payload);assert.equal(c.viewer_open(pointer,payload.length,1),1,error());}finally{c.viewer_free(pointer);}

 let previousOpportunity=-1,lastProgress=0,lastCallbackCount=0,lastCallbackAt=began,lastTerminalSample=0;const terminalSamples=[];
 while(frames<maximumFrames&&observed<maximumCallbacks&&performance.now()-began<maximumSeconds*1000){
  const now=performance.now(),delta=previousOpportunity<0?0:(now-previousOpportunity)/1000;previousOpportunity=now;
  const beforeTicks=c.frame_tick_count()>>>0,ok=c.frame(delta),after=performance.now();frames=c.frame_tick_count()>>>0;
  if(frames>beforeTicks){
   collect();
   const current=state();if(!lastState||[4,5,6,7,8,9,10,12,13,14].some(i=>current[i]!==lastState[i]))states.push({frame:frames,ms:after-began,words:current});lastState=current;
  }
  const current=lastState??state();
  if(observed!==lastCallbackCount){lastCallbackCount=observed;lastCallbackAt=after;}
  const end=Array.from(new Uint32Array(memory.buffer,c.campaign_end_state(),18));
  const atForcedMenu=end[0]===2&&end[1]===6&&end[2]===1&&end[3]===1&&end[4]===3&&end[6]===1&&end[7]===1&&end[8]===5&&end[16]===1;
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
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const rngTraceCount=c.observer_rng_count()>>>0,mainTraceCount=c.observer_main_count()>>>0;
assert(rngTraceCount<=256&&mainTraceCount===observed);
const rngTraceBytes=Buffer.from(new Uint32Array(memory.buffer,c.observer_rng_data(),rngTraceCount*16).slice().buffer);
const mainTraceBytes=Buffer.from(new Uint32Array(memory.buffer,c.observer_main_data(),mainTraceCount*8).slice().buffer);
writeFileSync(resolve(out,'rng-store-events.u32'),rngTraceBytes,{flag:'wx'});writeFileSync(resolve(out,'main-observer-times.u32'),mainTraceBytes,{flag:'wx'});
put('trace-report.json',{rngTraceCount,mainTraceCount,rngTraceSha256:sha(rngTraceBytes),mainTraceSha256:sha(mainTraceBytes),postStoreClockObserver:true,readOnly:true,noTargets:true,completeGame:false});
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
const captureComplete=stoppedBy==='campaign-forced-replay-menu-stable'&&!exception&&!errors.length;
const strict=false; // Cannot accept equivalence before the offline audit.
const report={schema:'th14/current-sakuyab-hard-full-campaign/1',referenceRowsReadDuringExecution:false,stableForcedReplayMenuObserved:stoppedBy==='campaign-forced-replay-menu-stable',terminal:true,pid:process.pid,stoppedBy,exception,errors,closed,frames,callbacks:observed,shotSnapshots:captured,elapsedSeconds:(performance.now()-began)/1000,firstRow,lastState,selectedDifferences:differences,cameraDifferences,hudDifferences,strictBoundedStatePassed:strict,comparisonPending:true,onlineReferenceCompared:false,comparedCallbacks:0,captureComplete,workers:pools.flatMap(p=>p.summary()),physicalWorkers:pools.flatMap(p=>p.physicalSummary()),processClockResolution:clock.state,actualColdApplicationInitializeTickAndDraw:true,actualAudioMixerSilentQueue:true,graphicsRecordingOnly:true,noDeclaredPerFileReadinessSchedule:true,productionCodeChanged:false,sourceIncludesUnpublishedSceneFilterAndAlphaRange:false,explicitHostedReplayOpen:true,startupClockProfileFromNormalCase:true,publishedVorbis18HashesVerified:true,frameTimesJsonOmittedBinaryDispatchRetained:true,allModesOrFullReplayAccepted:false,hardwarePixelsAccepted:false,audioEquivalent:false,completeGame:false,wasmSha256:sha(wasm),driverSha256:sha(read(import.meta.filename)),platformSha256:sha(read(resolve(root,'tools/th14-full-application-recording-platform-uniform2-nov13.mjs')))};
put('report.json',report);console.log(JSON.stringify({stoppedBy,callbacks:observed,frames,exception,selectedDifferences:differences,cameraDifferences,hudDifferences,strict}));if(!captureComplete)process.exitCode=1;
