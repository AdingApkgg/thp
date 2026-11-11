// Real threaded Application + native ANGLE. References are compared only after shutdown.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,statfsSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationGlesPlatform} from './th14-full-application-gles-transition-type0-nov09.mjs';
const entry='replay',slot=1,difficulty=1,mode='candidate',ordinary=false,caseName='current';
const root=resolve(import.meta.dirname,'..');
const evidence=resolve(root,'artifacts/th14/current-first-present-uv-repaint-nov12'),out=resolve(evidence,caseName);
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(p),load=p=>JSON.parse(read(p));
const component=resolve(evidence,'component');
const buildRaw=read(resolve(component,'build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(component,'candidate.wasm'));
assert(build.actualColdApplicationInitializeTickAndDraw&&build.noDeclaredPerFileReadinessSchedule);
assert.equal(sha(wasm),build.outputs.candidate.wasmSha256);
const fixture=build.fixturePath?resolve(root,build.fixturePath):resolve(component,'../fixture.cpp');
assert.equal(sha(read(fixture)),build.fixtureSha256);
for(const [p,h]of Object.entries(build.sourceBindingsByMode.candidate))assert.equal(sha(read(resolve(root,p))),h,p);
const linked=load(resolve(component,'actual-link-object-bindings.json'));for(const [p,h]of Object.entries(linked.actualLinkObjectBindings))assert.equal(sha(read(resolve(root,p))),h,p);
const referenceDirectory=resolve(root,'artifacts/th14/current-startup-prefix-nov10/native');
// Only this external startup profile/configuration is extracted before the run.
const referenceRaw=read(resolve(referenceDirectory,'report.json'));
const profile=(()=>{const r=JSON.parse(referenceRaw),a=r.rows.find(r=>r.kind==='native-Present-entry'&&r.stage===1);
 assert(r.frameReadbackCompleted&&r.actualPixelsCaptured&&a&&a.stage===1);
 return{ticks:a.originalInitialTicks,cookie:a.originalProcessCookie,configHex:r.configHex};})();
const asset=resolve(root,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f');
const assetRaw=read(resolve(asset,'manifest.json')),assetReport=JSON.parse(assetRaw);
assert(assetReport.passed&&assetReport.unchangedEntries===226);
assert.deepEqual(assetReport.changedEntries,['demo0.rpy']);
assert.equal(sha(read(assetReport.replayPath)),assetReport.replaySha256);
const archive=resolve(root,'artifacts/th14/node-gles-host-nov08/native-later/work/th14.dat'),archiveSha256=sha(read(archive));
assert.equal(archiveSha256,assetReport.originalArchiveSha256);
const runtime=resolve(root,'artifacts/th14/stable-stage-close-nov07/runtime-ready');
assert(statfsSync(root,{bigint:true}).bavail*statfsSync(root,{bigint:true}).bsize>=100n*1024n**3n);
if(process.argv.includes('--preflight')){const m=new WebAssembly.Module(wasm);assert(WebAssembly.Module.exports(m).some(x=>x.name==='diagnostic_uv_repaint'));assert(WebAssembly.Module.exports(m).some(x=>x.name==='diagnostic_uv_state'));console.log(JSON.stringify({preflight:true,wasmSha256:sha(wasm),providersVerified:true,noInstanceCreated:true}));process.exit(0);}
mkdirSync(out);mkdirSync(resolve(out,'save'));mkdirSync(resolve(out,'save/replay'));
const put=(name,value)=>writeFileSync(resolve(out,name),JSON.stringify(value,null,2)+'\n');
writeFileSync(resolve(out,'save/th14.cfg'),Buffer.from(profile.configHex,'hex'));
writeFileSync(resolve(out,'save/replay/th14_01.rpy'),read(assetReport.replayPath));
const bindings={};for(const p of [import.meta.filename,'tools/th14-full-application-gles-transition-type0-nov09.mjs','tools/th14-node-angle-context-nov08.mjs','tools/th14-node-wasm-gles-nov08.mjs','tools/th14-full-application-recording-platform-texture-units-v2-nov07.mjs','tools/th14-wasi-stage-pool-observer-clock-nov07.mjs']){
 const path=resolve(root,p),bytes=read(path);bindings[relative(root,path).replaceAll('\\','/')]=sha(bytes);
 writeFileSync(resolve(out,path.split(/[\\/]/).at(-1)),bytes);
}
put('plan.json',{pid:process.pid,wasmSha256:sha(wasm),buildSha256:sha(buildRaw),bindings,referenceMetadataSha256:sha(referenceRaw),profile,
 archiveSha256,maximumSeconds:90,maximumFrames:4000,trigger:{stage:1,firstActualPresentAfterFirstPlayer:true,configuredSkip:0},
 realApplication:true,realWasiThreads:true,actualGpu:true,originalArchiveUnmodified:true,privateDemo0Replacement:false,recordedInputAttractPath:false,ordinaryControlAcceptance:false,eachSideAttempts:1,assetManifestSha256:sha(assetRaw),replaySha256:assetReport.replaySha256,heldInput:0,warmAttractClear:false,
 hostPollRequestedMs:1,actualFrameCadence:true,noPerFileReadinessSchedule:true,noRngOrCounterPadding:true,
 originalGameplayRowsUsedAsInputs:false,comparisonOnlyAfterTerminal:true,counterfactualCapturedUvOnlyAfterEngineStop:true,noEngineUpdatesAfterCounterfactual:true,audibleOutput:false,completeGame:false});
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationGlesPlatform(module,memory,{clockInput:profile.ticks,archivePath:archive,fontDirectory:resolve(runtime,'fonts'),
 saveDirectory:resolve(out,'save'),angleDirectory:'C:/Users/APKGG/AppData/Local/Programs/Trae',onAsyncError:e=>errors.push(String(e?.stack??e))});
platform.env.th14_async_schedule_impl=(callback,data,delay)=>{
 assert(callback>0&&delay>=0&&delay<=60000);
 const token=setTimeout(()=>{platform.timers.delete(token);try{c.async_deliver_owned(callback,data);}catch(e){errors.push(String(e?.stack??e));}},delay);platform.timers.add(token);
};
let phase='platform-created';process.on('exit',code=>put('exit-event.json',{code,phase,gpuContextClosed:platform.context.closed}));
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(out,'save'),'/music':resolve(runtime,'music')},returnOnExit:true});
const instance=new WebAssembly.Instance(module,{observerhost:{now_ns:()=>process.hrtime.bigint()},env:platform.env,
 wasi_snapshot_preview1:{...wasi.wasiImport,proc_exit:code=>{throw Error('Guest proc_exit '+code+' at '+phase);}},
 wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool,'Prepared worker');return pool.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const words=(name,n)=>Array.from(new Uint32Array(memory.buffer,c[name](),n));
const error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
let frames=0,callbacks=0,created=false,closed=false,exception=null,capture=null,stoppedBy='unknown';
const states=[];let lastState=null,lastProgress=0,previous=-1;const began=performance.now();
try{
 if(ordinary)assert.equal(c.select_ordinary_entry(slot,difficulty),1);
 phase='application-initialize';c.shot_snapshot_enable(0);created=true;assert.equal(c.begin(profile.ticks,profile.cookie,0),1,error());
 assert.equal(platform.getError(),0,'GPU initialization');phase='application-frames';
 while(frames<4000&&performance.now()-began<90000){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count()>>>0,ok=c.frame(delta);frames=c.frame_tick_count()>>>0;
  assert(ok,error());assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   assert.equal(platform.getError(),0,'GPU frame '+frames);callbacks=c.observation_count()>>>0;
   const state=words('state',16);
   if(!lastState||state.some((v,i)=>v!==lastState[i]))states.push({frame:frames,ms:performance.now()-began,words:state});lastState=state;
   if(callbacks){
    const n=c.observation_words()>>>0;assert.equal(n,callbacks*114);
    const row=Array.from(new Uint32Array(memory.buffer,c.observation_data()+(callbacks-1)*114*4,114));
    if(row[31]===1&&(ordinary||row[112]===1)&&c.frame_gate_counter()===0){
     c.selected_sht_target();
     assert(row[1]>=1,'First actual gameplay Present');
     assert.equal(c.frame_gate_config(),0);assert.equal(c.recorded_skip_config(),0);assert.equal(c.host_audio_flags()&16,0);assert.equal(c.recorded_audio_flags()&16,0);assert.equal(c.cached_battle_audio_flags()&16,0);assert.equal(c.sample_actual_controller_without_device(),0);phase='target-readback';
     const copyWords=c.compositor_state_capture()>>>0;assert(copyWords>2);
     put('world-camera-after-draw.json',{readOnly:true,nativeOrder75:true,words:Array.from(new Uint32Array(memory.buffer,c.world_camera_capture(),75))});
     put('compositor-after-draw.json',{readOnly:true,words:Array.from(new Uint32Array(memory.buffer,c.compositor_state_data(),copyWords))});
     const tw=c.type0_capture()>>>0;assert(tw===2||tw===7+6*303);put('transition-after-draw.json',{readOnly:true,words:Array.from(new Uint32Array(memory.buffer,c.type0_data(),tw))});
     const vmWords=c.gpu_target_capture()>>>0;assert(vmWords>=6);
     const vmBytes=Buffer.from(new Uint32Array(memory.buffer,c.gpu_target_data(),vmWords).slice().buffer);
     writeFileSync(resolve(out,'target-live-vms.u32'),vmBytes,{flag:'wx'});
     put('target-live-vms.json',{words:vmWords,header:Array.from(new Uint32Array(vmBytes.buffer,vmBytes.byteOffset,6)),sha256:sha(vmBytes),readOnly:true,postDraw:true});
     const pixels=platform.readBGRA();writeFileSync(resolve(out,'application-first-present.bgra'),pixels,{flag:'wx'});
     assert.equal(callbacks,1);assert.equal(row[1],1);
     const uvState=()=>{const pointer=c.diagnostic_uv_state();assert(pointer);return Array.from(new Uint32Array(memory.buffer,pointer,12));};
     const actualState=uvState(),repaints=[];
     const changed=(a,b)=>{assert.equal(a.length,b.length);let n=0;for(let i=0;i<a.length;i+=4)if(!a.subarray(i,i+4).equals(b.subarray(i,i+4)))++n;return n;};
     const repaint=(mode,name,x=0,y=0)=>{
      const before=uvState();assert.equal(c.diagnostic_uv_repaint(mode,x,y),1,error());assert.equal(platform.getError(),0);
      const after=uvState();for(const i of [0,1,2,3,4,7,8,9,10])assert.equal(after[i],before[i],'No update/RNG advance during repaint');
      const image=platform.readBGRA();writeFileSync(resolve(out,name+'.bgra'),image,{flag:'wx'});
      repaints.push({mode,name,before,after,pixelSha256:sha(image),differentPixelsFromActual:changed(pixels,image)});return image;
     };
     const control=repaint(0,'control-repeat');
     if(!control.equals(pixels)){put('uv-repaint-control-rejection.json',{repaints,actualState,idempotent:false,counterfactualNotAttempted:true});throw Error('Repeated draw changed pixels; reject UV counterfactual');}
     // Reference UV words are diagnostic inputs after the live frame stops.
     const nativeGeometryRaw=read(resolve(referenceDirectory,'transition-before-readback.json'));
     const nativeGeometry=Buffer.from(JSON.parse(nativeGeometryRaw).geometryHex,'hex');assert.equal(nativeGeometry.length,5*1484+8);
     const uv=[nativeGeometry.readUInt32LE(4*1484+0x88),nativeGeometry.readUInt32LE(4*1484+0x8c)];
     const patched=repaint(1,'counterfactual-native-uv',...uv);
     const restored=repaint(2,'restored-original-uv');
     put('uv-repaint.json',{actualState,repaints,capturedUv:uv,nativeGeometrySha256:sha(nativeGeometryRaw),
      idempotentControl:true,restoredPixelsExact:restored.equals(pixels),restoredStateExact:JSON.stringify(uvState())===JSON.stringify(actualState),
      counterfactualOnly:true,strictActualPixelsAcceptanceUnchanged:true,completeGame:false});
     assert(restored.equals(pixels),'Restore must reproduce actual first-Present pixels');assert.deepEqual(uvState(),actualState);
     capture={frames,callbacks,latestBeforePlayerRow:row,state,closeGate:words('close_gate_state',20),pixelSha256:sha(pixels),pixelBytes:pixels.length,
      actualGpuAfterFullApplicationFrameCommit:true,renderSkipCounter:c.frame_gate_counter(),runtimeHostSkip:c.frame_gate_config(),runtimeRecordedSkip:c.recorded_skip_config(),configuredSkip:0,hostAudioFlags:c.host_audio_flags(),recordedAudioFlags:c.recorded_audio_flags(),cachedBattleAudioFlags:c.cached_battle_audio_flags(),originalPixelsSuppliedToEngine:false};
     put('capture.json',capture);stoppedBy='declared-target';break;
    }
   }
  }
  if(performance.now()-began-lastProgress>10000){lastProgress=performance.now()-began;put('progress.json',{pid:process.pid,frames,callbacks,state:lastState,elapsedSeconds:lastProgress/1000});console.log(JSON.stringify({frames,callbacks,state:lastState}));}
  await new Promise(r=>setTimeout(r,1));
 }
 if(stoppedBy==='unknown')stoppedBy=frames>=6500?'frame-limit':'wall-limit';
}catch(e){exception=String(e?.stack??e);stoppedBy='exception';}
finally{
 phase='application-close';
 try{if(created){
  writeFileSync(resolve(out,'observations.u32'),Buffer.from(new Uint32Array(memory.buffer,c.observation_data(),c.observation_words()).slice().buffer));
  const n=c.live_vm_prefix_size()>>>0;assert(n<=5*(6+8192*303));writeFileSync(resolve(out,'live-vm-prefix.u32'),Buffer.from(new Uint32Array(memory.buffer,c.live_vm_prefix_data(),n).slice().buffer));
  put('initial-history.json',{readOnlyBeforeActualTick:true,scalarRngReadsNotAtomicPair:true,stride:24,fields:['screen','substate','timer','held','phase','scriptSeed','scriptCalls','visualSeed','visualCalls','rootHandle','rootAge','rootCounter','rootState','rootLayer','signaturePresent','signatureDraws','bootStageOwner','bootUploadIndex','controlPresent','controlFlags','controlCallbacksEnabled','battlePresent','stage','stageFrame'],words:Array.from(new Uint32Array(memory.buffer,c.ui_history_data(),c.ui_history_words()))});
  writeFileSync(resolve(out,'menu-inputs.u32'),Buffer.from(new Uint32Array(memory.buffer,c.ui_input_data(),c.ui_input_words()).slice().buffer));
  put('music-history.json',{stride:8,fields:['inputHistoryIndex','rootAge','rootCounter','scriptCalls','command','argument','progress','controlFlags'],words:words('music_history_data',c.music_history_words()),readOnly:true,queueCriticalSectionObserved:true});
  const shtCount=c.selected_sht_count()>>>0;assert(shtCount<=16);
  put('selected-sht-owner.json',{stride:build.observationStride,fields:build.observationFields,rows:shtCount,words:Array.from(new Uint32Array(memory.buffer,c.selected_sht_data(),shtCount*build.observationStride)),readOnly:true});
  c.close();closed=true;
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);
 }}catch(e){exception??=String(e?.stack??e);}
 try{await Promise.all(pools.map(p=>p.shutdown()));clock.close();}catch(e){exception??=String(e?.stack??e);}
 try{put('platform-before-gpu-close.json',platform.summary());assert.equal(platform.getError(),0,'GPU teardown');}catch(e){exception??=String(e?.stack??e);}
 platform.closeGpu();
}
phase='terminal-audit';put('application-states.json',states);
const services=platform.summary();put('platform.json',services);
const resourceLeaks=Object.entries(services.actualNativeGles.liveObjects).filter(([,n])=>n!==0);
const platformRetired=!services.window&&!services.context&&!services.stream&&!services.openFiles&&!services.pendingTimers;
let comparison=null;
if(capture&&!ordinary){
 const native=JSON.parse(referenceRaw),target=native.rows.find(r=>r.kind==='native-Present-entry'&&r.stage===1),
  expected=read(resolve(referenceDirectory,native.readback.file)),actual=read(resolve(out,'application-first-present.bgra'));
 assert.equal(sha(expected),native.readback.pixelSha256);assert.equal(actual.length,expected.length);
 const byChannel=[0,0,0,0],bounds=[640,480,-1,-1],first=[];let differentPixels=0,differentBytes=0,maximumError=0;
 for(let p=0;p<actual.length;p+=4){let diff=false;for(let k=0;k<4;k++)if(actual[p+k]!==expected[p+k]){
  ++differentBytes;++byChannel[k];diff=true;maximumError=Math.max(maximumError,Math.abs(actual[p+k]-expected[p+k]));
  if(first.length<12)first.push({x:p/4%640,y:Math.floor(p/4/640),channel:k,actual:actual[p+k],expected:expected[p+k]});
 }if(diff){++differentPixels;const x=p/4%640,y=Math.floor(p/4/640);bounds[0]=Math.min(bounds[0],x);bounds[1]=Math.min(bounds[1],y);bounds[2]=Math.max(bounds[2],x);bounds[3]=Math.max(bounds[3],y);}}
 const selected=capture.latestBeforePlayerRow.slice(1,33),selectedDifferences=[],selectedFields={};
 for(const [name,cppIndex,nativeIndex]of [['character',27,0],['subtype',28,1],['difficulty',29,3],['scoreUnits',12,2],['power',15,12],['lives',16,15]]){
  selectedFields[name]={cpp:selected[cppIndex],native:target.selectedGlobalWords[nativeIndex]};
  if(selectedFields[name].cpp!==selectedFields[name].native)selectedDifferences.push({name,...selectedFields[name]});
 }
 comparison={nativeControllerFrame:target.stageFrame,cppControllerFrame:capture.latestBeforePlayerRow[1],controllerFrameExact:target.stageFrame===capture.latestBeforePlayerRow[1],nativeConfiguredSkip:target.configuredFrameSkip,nativeRenderSkipCounter:target.renderSkipCounter,comparedBytes:actual.length,differentBytes,differentPixels,byChannel,bounds,maximumError,first,
  pixelsExact:differentBytes===0,actualSha256:sha(actual),nativeSha256:sha(expected),selectedFields,selectedBeforePlayerDifferences:selectedDifferences,
  nativePresentRngHex:target.rngHex,cppAfterFrameRng:capture.closeGate.slice(14,18),
  beforePlayerAndPresentAreDistinctObservationBoundaries:true,referenceDebuggerAffectsLoadingTiming:true,completeGame:false};
 put('comparison.json',comparison);
}
const selected=capture?.latestBeforePlayerRow.slice(1,33),ordinaryEntryMatched=ordinary&&!!selected&&selected[27]===Math.floor(slot/2)&&selected[28]===slot%2&&selected[29]===difficulty&&selected[15]===100;
const report={entry,slot,difficulty,ordinaryEntryMatched,ordinaryFirstPlayer:selected??null,selectedShtOwnershipProbe:true,terminal:true,pid:process.pid,stoppedBy,exception,errors,frames,callbacks,closed,platformRetired,resourceLeaks,
 gpuContextClosed:platform.context.closed,workers:pools.flatMap(p=>p.summary()),physicalWorkers:pools.flatMap(p=>p.physicalSummary()),
 processClockResolution:clock.state,captureComplete:!!capture&&!exception&&!errors.length,comparison,
 counterfactualUvRepaintAfterFirstFrame:true,noLiveEngineUpdatesAfterCounterfactual:true,boundedDiagnosticOnly:true,actualColdApplication:true,actualGpu:true,audibleOutput:false,completeGame:false,elapsedSeconds:(performance.now()-began)/1000};
put('report.json',report);phase='finished';console.log(JSON.stringify({stoppedBy,frames,callbacks,exception,resourceLeaks,platformRetired,differentPixels:comparison?.differentPixels}));
if(!report.captureComplete||resourceLeaks.length||!platformRetired||(ordinary&&!ordinaryEntryMatched))process.exitCode=1;
