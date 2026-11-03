import{gunzipSync}from'node:zlib';
import assert from'node:assert/strict';import{readFileSync as read,writeFileSync as write,mkdirSync as mkdir,existsSync as exists}from'node:fs';
import{resolve,dirname,basename,relative,isAbsolute}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
// Explicit case inputs; no native gameplay state is supplied to the engine.
const allowed=new Set(['native','assets','build','wasm','output','prefix','selection','hud-ready','publication-cutoff','scheduler-phases','scene-copy-observation','normal-boundary-observation','normal-vm-boundary-observation','vm-boundary-baseline']);
const options=new Map();for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i]?.replace(/^--/,'');assert(allowed.has(key)&&process.argv[i+1]&&!options.has(key),'Unknown, repeated or missing option '+key);options.set(key,process.argv[i+1]);}
for(const key of ['native','assets','build','output','selection'])assert(options.has(key),'Missing --'+key);
const root=resolve(import.meta.dirname,'..'),nativeHome=resolve(root,options.get('native')),nativeName=basename(nativeHome),mode='initial-worker-events',home=dirname(resolve(root,options.get('build')));
const sha=b=>createHash('sha256').update(b).digest('hex'),prefix=Number(options.get('prefix')??0),publicationCutoff=Number(options.get('publication-cutoff')??1000),expectedSelection=options.get('selection').split(',').map(Number),hudFlag=(options.get('hud-ready')??'cpu-write')==='cpu-write'?'-cpu-write':'-main-resource-boundary';
assert(Number.isInteger(prefix)&&prefix>=0&&Number.isInteger(publicationCutoff)&&publicationCutoff>0);
assert(expectedSelection.length===4&&expectedSelection.every(Number.isInteger));assert(['cpu-write','boundary'].includes(options.get('hud-ready')??'cpu-write'));
const schedulerPhases=options.get('scheduler-phases')??'legacy';assert(['legacy','observed','resource-player'].includes(schedulerPhases));
const phasedScheduler=schedulerPhases!=='legacy';
const out=resolve(root,options.get('output')),scope=relative(resolve(root,'artifacts/th14'),out);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope),'New TH14 artifact directory required');
const nativeReport=exists(resolve(nativeHome,'report.json'))?JSON.parse(read(resolve(nativeHome,'report.json'))):null,initial=JSON.parse(read(resolve(nativeHome,'untouched-first-player.json')));
const snapshotPlan=exists(resolve(nativeHome,'snapshot-plan.json'))?JSON.parse(read(resolve(nativeHome,'snapshot-plan.json'))):null;
const snapshotCallbacks=snapshotPlan?.callbacks??[1,26000,30000,36000,38900,60000,90000,120000];
assert(snapshotCallbacks.length<=32&&snapshotCallbacks[0]===1&&snapshotCallbacks.every((value,index)=>Number.isInteger(value)&&value>0&&(!index||value>snapshotCallbacks[index-1])));
if(nativeReport)assert.equal(nativeReport.anmPublicationTraceCutoffPlayerCallbacks,publicationCutoff,'Declared publication cutoff differs from capture');
const progress=nativeReport??JSON.parse(read(resolve(nativeHome,'progress.json'))),limit=prefix||nativeReport?.callbacks;assert(limit&&progress.callbacks>=limit);assert.deepEqual(initial.words.slice(27,31),expectedSelection);
if(!prefix){assert(nativeReport.observedForcedReplayEndMenu&&nativeReport.childExited&&!nativeReport.error&&nativeReport.gameStateWordWrites===1&&!nativeReport.rngOrCounterWrites);assert(nativeReport.caseInitialization.attractBitClearOnly);assert(nativeReport.caseInitialization.beforeFlags&0x40);assert.equal(nativeReport.caseInitialization.afterFlags,nativeReport.caseInitialization.beforeFlags&~0x40);}
const events=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x)).filter(x=>x.hostMonotonicNs<=initial.hostMonotonicNs),frames=events.filter(x=>x.event==='main-resource-pump'),native=read(resolve(nativeHome,'allocation-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x));
const flags=['signature-ready-flag-published','ascii-ready-flag-published'].map(k=>events.find(x=>x.event===k));assert(flags.every(Boolean));
const origin=BigInt(frames[0].hostMonotonicNs);assert(!exists(out));mkdir(out,{recursive:true});
const wasm=read(resolve(root,options.get('wasm')??resolve(home,'observer.wasm'))),build=JSON.parse(read(resolve(root,options.get('build'))));assert.equal(sha(wasm),build.wasmSha256);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
if(c.observation_snapshot_target){for(let at=0;at<32;at++)assert.equal(c.observation_snapshot_target(at,snapshotCallbacks[at]??0),1);}
else assert.deepEqual(snapshotCallbacks,[1,26000,30000,36000,38900,60000,90000,120000],'Observer build does not support configured snapshot targets');
const assetHome=resolve(root,options.get('assets')),assetManifest=JSON.parse(read(resolve(assetHome,'manifest.json')));
assert(assetManifest.passed&&assetManifest.unchangedEntries===226);assert.deepEqual(assetManifest.changedEntries,['demo0.rpy']);
const replayBytes=read(resolve(root,assetManifest.replayPath));assert.equal(sha(replayBytes),assetManifest.replaySha256);assert(/^[a-f0-9]{64}$/.test(assetManifest.replaySha256));
if(nativeReport)assert.equal(nativeReport.sourceFullReplaySha256,assetManifest.replaySha256);
const archive=read(resolve(assetHome,'th14.dat'));assert.equal(sha(archive),assetManifest.referenceArchiveSha256);const p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);assert.equal(c.cold_begin(initial.actualInitialTimeGetTimeInput),1);assert.equal(c.reference_environment(initial.actualOriginalSecurityCookie,0x1aec84),1);
assert.equal(c.cold_host_warm_at_first_player(),1);const configured=[];
for(const e of events.filter(x=>x.event==='cpu-resource-queued')){assert.equal(c.cold_host_queue(e.queuedFile,BigInt(e.hostMonotonicNs)-origin),1);configured.push({file:e.queuedFile,hostMonotonicNs:e.hostMonotonicNs});}
assert.equal(c.cold_host_flags(BigInt(flags[0].hostMonotonicNs)-origin,BigInt(flags[1].hostMonotonicNs)-origin),1);
if(mode==='initial-worker-events'){
 const title=events.find(x=>x.event==='title-ready-flag-published');assert(title);
 assert.equal(c.cold_host_title_ready(BigInt(title.hostMonotonicNs)-origin),1);
}
const explicitFiles=new Set(configured.map(x=>x.file));
for(const f of frames)for(const slot of f.resourceSlots)if(slot.wait&&!explicitFiles.has(slot.file)){
 assert.equal(c.cold_host_queue(slot.file,BigInt(f.hostMonotonicNs)-origin),1);explicitFiles.add(slot.file);
 configured.push({file:slot.file,hostMonotonicNs:f.hostMonotonicNs,firstObservedPendingAtMainBoundary:true});
}
const initialPlayer=events.find(x=>x.event==='initial-player-file-returned'),initialWorker=events.find(x=>x.event==='initial-control-loading-flag-cleared');assert(initialPlayer&&initialWorker);
assert.equal(c.cold_host_initial_worker_ready(BigInt(initialWorker.hostMonotonicNs)-origin),1);
const asciiEvents=JSON.parse(read(resolve(nativeHome,'ascii-create-call-events.json')));assert(asciiEvents.actualCallInstruction&&asciiEvents.rows.length===1);const asciiBegin=asciiEvents.rows[0];assert.equal(asciiBegin.pc,0x44477a);assert.equal(asciiBegin.callTarget,0x47ed10);let asciiDelivered=false,asciiDeliveryResult=0;
const portable=[];let last=0,entry=null,hostPlayerDone=false,hostRetireDone=false;const sigRetire=events.find(x=>x.event==='title-worker-signature-retirement');assert(sigRetire);
const collect=frame=>{const end=c.cold_creation_count();if(entry&&c.public_replay_observations()>publicationCutoff){last=end;return;}assert(end>=last&&end-last<=4096);const ordinals=new Set();
for(let n=last;n<end;n++){const f=Array.from({length:6},(_,k)=>c.cold_creation_value(n,k)>>>0),serial=f[5]>>>13;assert(serial>0);const publicationOrdinal=serial+Math.max(0,Math.ceil((last+1-serial)/0x7ffff))*0x7ffff;assert(publicationOrdinal>last&&publicationOrdinal<=end);assert(!ordinals.has(publicationOrdinal));ordinals.add(publicationOrdinal);portable.push({creationIndex:n+1,publicationOrdinal,mainResourceFrame:frame,callbackBoundary:entry?frame:0,serial,handle:f[5],file:f[2],script:f[0],requestedLayer:f[1]});}assert.equal(ordinals.size,end-last);last=end;};

for(let i=0;i<frames.length;i++){
 if(!hostRetireDone&&frames[i].hostMonotonicNs>=sigRetire.hostMonotonicNs){assert.equal(c.cold_host_signature_retire(BigInt(sigRetire.hostMonotonicNs)-origin),1);collect(i);hostRetireDone=true;}
 if(!hostPlayerDone&&frames[i].hostMonotonicNs>=initialPlayer.hostMonotonicNs){assert.equal(c.cold_host_initial_player(BigInt(initialPlayer.hostMonotonicNs)-origin),1);collect(i);hostPlayerDone=true;}
 assert.equal(c.cold_tick(BigInt(frames[i].hostMonotonicNs)-origin),1);c.probe_retire_capture();collect(i+1);
 if(!asciiDelivered&&asciiBegin.hostMonotonicNs>=frames[i].hostMonotonicNs&&asciiBegin.hostMonotonicNs<(frames[i+1]?.hostMonotonicNs??Infinity)){asciiDeliveryResult=c.cold_host_ascii_draw_begin(BigInt(asciiBegin.hostMonotonicNs)-origin);assert([1,2].includes(asciiDeliveryResult));collect(i+1);asciiDelivered=true;}
 if(c.cold_state(0)===1&&c.cold_state(1)){entry={mainResourceFrame:i+1,state:Array.from({length:16},(_,n)=>c.cold_state(n)>>>0)};break;}
}

assert(entry);assert.equal(c.public_replay_observations(),1);
const nativeRaw=read(resolve(nativeHome,'selected-state.u32')).subarray(0,limit*128),times=read(resolve(nativeHome,'player-host-monotonic.u64')).subarray(0,limit*8);
assert.equal(nativeRaw.length,limit*128);assert.equal(times.length,limit*8);if(!prefix){assert.equal(sha(nativeRaw),nativeReport.selectedSha256);assert.equal(sha(times),nativeReport.playerHostTimesSha256);}
write(resolve(out,'native-selected-state.u32'),nativeRaw,{flag:'wx'});write(resolve(out,'native-times.u64'),times,{flag:'wx'});
const maxStage=nativeRaw.readUInt32LE((limit-1)*128+30*4);
const cameraRaw=read(resolve(nativeHome,'world-camera.raw')).subarray(0,limit*0x124);assert.equal(cameraRaw.length,limit*0x124);const cameraRows=[],cameraCounts={},cameraFirst={};let allocationBoundaryCount=0,lateStartCount=0,lateEndCount=0,initialCreationCount=0;const hudRows=[],hudCounts={},hudFirst={};const hudRaw=read(resolve(nativeHome,'hud-score.u32')).subarray(0,limit*8);assert.equal(hudRaw.length,limit*8);const cameraOffsets=[...Array.from({length:22},(_,i)=>i*4),0x104,0x108,0x10c];
const rows=[],counts={},first={};const unsupportedObservations=[];let unsupportedMask=0,unsupportedNativeMask=0;let firstDifference=null,lastNow=BigInt(frames[entry.mainResourceFrame-1].hostMonotonicNs)-origin;
const playerOrigin=times.readBigUInt64LE(0),baseNow=lastNow;
const transition=(exists(resolve(nativeHome,'transition-events.jsonl'))?read(resolve(nativeHome,'transition-events.jsonl'),'utf8').trim().split('\n').filter(Boolean).map(x=>JSON.parse(x)):[]);
const resourceEvents=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x)),phaseInputs=[];
// A first-stage prefix has no transition worker yet. The capture creates these
// files at its first event; absence is valid only when every sampled row is
// still in stage1. Later-stage cases keep their mandatory observation reads.
const stageEvents=name=>{const path=resolve(nativeHome,name);if(!exists(path)){assert.equal(maxStage,1,'Missing later-stage observation '+name);return [];}return read(path,'utf8').trim().split('\n').filter(Boolean).map(x=>JSON.parse(x));};
const sceneEvents=phasedScheduler?stageEvents('scene-camera-copy-events.jsonl'):[];
const controllerEvents=schedulerPhases==='observed'?stageEvents('controller-phase-events.jsonl'):[];
const controlClock=new Map(),pumpClock=new Map(),beforeDrawWorker=new Map(),afterDrawWorker=new Map(),sceneNextCameraClock=new Map(),sceneUpdateHandoffs=[],sceneCopyWordHandoffs=[],sceneWordDelivery=new Map();
if(options.has('scene-copy-observation')){
 assert(phasedScheduler&&prefix===15000,'The explicit TF observation is a finite15000-callback prefix only');
 const proof=JSON.parse(read(resolve(root,options.get('scene-copy-observation'))));
 assert(proof.verifiedFiniteOriginalSceneCopyObservation&&proof.diagnosticPrefixOnly&&proof.callbacks===prefix);
 assert(!proof.completeGame&&!proof.nativeEquivalent&&!proof.oldCameraFailureClosed);
 assert.equal(proof.verifierSha256,sha(read(resolve(root,'tools/th14-scene-copy-word-evidence-oct26.py'))));
 for(const[path,row]of Object.entries(proof.bindings))assert.equal(sha(read(resolve(root,path))),row.sha256,'Observation binding changed: '+path);
 const nativeKey=relative(root,resolve(nativeHome,'report.json')).replaceAll('\\','/');assert.equal(proof.bindings[nativeKey]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
 const words=read(resolve(nativeHome,'scene-camera-word-copy-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x));
 assert.equal(words.length,3);assert.deepEqual(words.map(row=>row.word),[0,1,2]);
 const stage=words[0].stage,callback=words[0].precedingPlayerCallbacks;
 const before=sceneEvents.find(row=>row.stage===stage&&row.event==='scene-camera-copy-before');
 assert(before&&before.precedingPlayerCallbacks===callback&&before.mainPhaseAtObservation==='draw');
 const boundaries=words.map(row=>row.lastMainCameraBoundary);
 for(const[row,boundary]of words.map((row,index)=>[row,boundaries[index]])){
  assert(row.readOnly&&row.exactTrapFlagStep&&row.actualOriginalRepIterationObserved&&!row.nativeValuesProvidedToEngine);
  assert.equal(row.stage,stage);assert.equal(row.precedingPlayerCallbacks,callback);assert.equal(row.threadId,before.threadId);assert.equal(row.scene,before.scene);
  assert(boundary?.readOnly&&boundary.event==='world-perspective-right-written'&&boundary.pc===0x4465a6&&boundary.mainPhaseAtObservation==='draw');
  assert.equal(boundary.precedingPlayerCallbacks,callback);assert.equal(boundary.stage,stage);
  assert(before.hostMonotonicNs<boundary.hostMonotonicNs&&boundary.hostMonotonicNs<row.hostMonotonicNs);
 }
 // Use only observed instruction boundaries and time, never source/copy values.
 const delivery={stage,callback,readyNs:words[0].hostMonotonicNs,completionSource:'originalRightWordTrapAfterObservedPerspectiveBoundary',perspectiveBoundaryNs:boundaries[0].hostMonotonicNs};
 sceneWordDelivery.set(stage,delivery);sceneCopyWordHandoffs.push(delivery);
}
if(phasedScheduler){
 assert(c.observed_player_boundary&&c.observed_worker_boundary&&c.observed_boundary_ok,'Observer lacks callback-boundary support');
 for(const e of controllerEvents){assert.equal(e.pc,0x436bed);const callback=e.precedingPlayerCallbacks+1;assert(!controlClock.has(callback),'Repeated controller boundary requires its own scheduler observation');controlClock.set(callback,e.hostMonotonicNs);}
 for(const e of resourceEvents.filter(x=>x.event==='main-resource-pump')){
  let low=0,high=limit;while(low<high){const mid=(low+high)>>>1;if(times.readBigUInt64LE(mid*8)<BigInt(e.hostMonotonicNs))low=mid+1;else high=mid;}
  if(low>0&&low<limit)pumpClock.set(low+1,e.hostMonotonicNs);
 }
 const cameraBoundaryEvents=exists(resolve(nativeHome,'camera-boundary-events.jsonl'))?read(resolve(nativeHome,'camera-boundary-events.jsonl'),'utf8').trim().split('\n').filter(Boolean).map(x=>JSON.parse(x)):[];
 const copies=sceneEvents.filter(x=>x.event==='scene-camera-copy-before'||x.event==='scene-camera-copy-after'&&!sceneEvents.some(b=>b.stage===x.stage&&b.event==='scene-camera-copy-before'));
 for(const e of copies){
  const callback=e.precedingPlayerCallbacks;if(callback<1||callback>limit)continue;
  const wordDelivery=sceneWordDelivery.get(e.stage);
  if(wordDelivery){assert.equal(wordDelivery.callback,callback);assert(!afterDrawWorker.has(callback));afterDrawWorker.set(callback,wordDelivery.readyNs);continue;}
  let phase=e.mainPhaseAtObservation;
  if(phase===undefined){const playerTime=Number(times.readBigUInt64LE((callback-1)*8));const pumps=resourceEvents.filter(x=>x.event==='main-resource-pump'&&x.hostMonotonicNs<=e.hostMonotonicNs);assert(pumps.length,'No observed resource boundary for Scene event');phase=pumps.at(-1).hostMonotonicNs>playerTime?'update':'draw';}
  const boundary=e.lastMainCameraBoundary;
  // A resource pump starts the next update before the controller replaces the
  // camera left by the previous draw. Deliver Scene in that observed window.
  // Only instruction boundaries and timestamps are used, never camera values.
  if(phase==='update'&&boundary?.event==='world-perspective-right-written'&&boundary.precedingPlayerCallbacks===callback&&callback<limit){
   assert(e.readOnly&&boundary.readOnly&&boundary.mainPhaseAtObservation==='draw');
   assert.equal(e.pc,e.event==='scene-camera-copy-before'?0x40d435:0x40d447);
   assert.equal(boundary.stage,e.stage);assert.equal(boundary.pc,0x4465a6);
   const next=cameraBoundaryEvents.find(b=>b.event==='controller-camera-published'&&b.precedingPlayerCallbacks===callback&&b.hostMonotonicNs>e.hostMonotonicNs);
   assert(next,'Missing observed next camera publication after cross-update Scene copy');
   assert(next.readOnly&&next.mainPhaseAtObservation==='update');assert.equal(next.pc,0x40dae9);assert.equal(next.stage,e.stage);assert.equal(next.threadId,boundary.threadId);
   assert(Number(times.readBigUInt64LE((callback-1)*8))<boundary.hostMonotonicNs&&boundary.hostMonotonicNs<e.hostMonotonicNs&&next.hostMonotonicNs<=Number(times.readBigUInt64LE(callback*8)),'Scene handoff must lie between consecutive observed Player callbacks');
   assert(!afterDrawWorker.has(callback)&&!sceneNextCameraClock.has(callback+1));
   afterDrawWorker.set(callback,e.hostMonotonicNs);sceneNextCameraClock.set(callback+1,next.hostMonotonicNs);
   sceneUpdateHandoffs.push({stage:e.stage,precedingPlayerCallbacks:callback,drawCameraBoundaryNs:boundary.hostMonotonicNs,sceneCopyNs:e.hostMonotonicNs,nextControllerCameraNs:next.hostMonotonicNs});continue;
  }
  if(phase!=='draw')continue;
  assert(boundary,'Missing camera scheduler boundary');
  const map=boundary.event==='world-perspective-right-written'?afterDrawWorker:beforeDrawWorker;
  assert(!map.has(e.precedingPlayerCallbacks));map.set(e.precedingPlayerCallbacks,e.hostMonotonicNs);
 }
}
for(let stage=2;stage<=maxStage;stage++){
 const call=transition.find(x=>x.event==='sleep60-before-call'&&x.stage===stage),returned=transition.find(x=>x.event==='sleep60-returned'&&x.stage===stage);assert(call&&returned&&returned.returnInstructionObservedDirectly);
 assert.equal(c.observed_worker_events(stage,baseNow+BigInt(call.hostMonotonicNs)-playerOrigin,baseNow+BigInt(returned.hostMonotonicNs)-playerOrigin),1);
 if(phasedScheduler){
  const initialized=transition.find(x=>x.event==='replay-seeds-restored-before-globals-copy'&&x.stage===stage);
  if(initialized){assert.equal(initialized.pc,0x456133);assert(initialized.originalInstructionBytes.startsWith('f3a5'));assert.equal(c.observed_worker_initialize(stage,baseNow+BigInt(initialized.hostMonotonicNs)-playerOrigin),1);phaseInputs.push({stage,phase:'Initialize',readyNs:initialized.hostMonotonicNs,completionSource:'original456133AfterSeedsRestoredBeforeGlobalsCopy',globalCopyAlreadyCompletedNotAsserted:true});}
 }
 const nextCall=transition.find(x=>x.event==='sleep60-before-call'&&x.stage===stage+1),end=nextCall?.hostMonotonicNs??Infinity;
 const later=resourceEvents.filter(x=>x.hostMonotonicNs>=call.hostMonotonicNs&&x.hostMonotonicNs<end),frames=later.filter(x=>x.event==='main-resource-pump'),inputs=[];
 for(const[phase,file,name]of[['Hud',6,'st'+String(stage).padStart(2,'0')+'logo.anm'],['Scene',(stage&1)+3,'st'+String(stage).padStart(2,'0')+'wl.anm']]){
  const queued=later.find(x=>x.event==='cpu-resource-queued'&&x.queuedFile===file);
  const firstObserved=frames.find(x=>x.resourceSlots.some(v=>v.file===file&&v.name===name));assert(queued||firstObserved,'No resource observation '+stage+' '+phase);
  const ready=frames.find(x=>x.hostMonotonicNs>=(queued?.hostMonotonicNs??firstObserved.hostMonotonicNs)&&x.resourceSlots.some(v=>v.file===file&&v.name===name&&v.wait===0));assert(ready,'Missing ready '+stage+' '+phase);
  let readyNs=ready.hostMonotonicNs,completionSource='firstObservedResourceReadyMainBoundary';
  if(phase==='Hud'&&hudFlag==='-cpu-write'){
   const writes=read(resolve(nativeHome,'hud-initialization-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x));
   const written=writes.find(x=>x.event==='hud-score-initialization-after-write'&&x.stage===stage);assert(written);readyNs=written.hostMonotonicNs;completionSource='original42ec6bAfterHudInitializationWrite';
  }
  if(phase==='Scene'&&phasedScheduler){
   const before=sceneEvents.find(x=>x.event==='scene-camera-copy-before'&&x.stage===stage),after=sceneEvents.find(x=>x.event==='scene-camera-copy-after'&&x.stage===stage);
   assert(after&&(schedulerPhases!=='observed'||before)&&(!before||before.hostMonotonicNs<=after.hostMonotonicNs),'Missing original Scene copy boundaries '+stage);
   readyNs=(before??after).hostMonotonicNs;completionSource=before?'original40d435BeforeSceneCameraCopy':'original40d447AfterSceneCameraCopy';
   const words=sceneWordDelivery.get(stage);if(words){readyNs=words.readyNs;completionSource=words.completionSource;}
  }
  inputs.push({stage,phase,file,queuedNs:queued?.hostMonotonicNs??null,queueObservedDirectly:!!queued,resourceFirstObservedNs:firstObserved?.hostMonotonicNs??null,readyNs,completionSource,boundedByFirstObservedReadyMainBoundary:completionSource==='firstObservedResourceReadyMainBoundary'});
 }
 const timelineWrite=later.find(x=>x.event==='initial-control-loading-flag-cleared'&&x.stage===stage&&x.observedOriginalLoadingFlagClear);
 const timeline=timelineWrite??frames.find(x=>!(x.controlFlags&4));assert(timeline,'Missing Timeline ready '+stage);
 if(timelineWrite)assert.equal(timelineWrite.clearInstructionBytes,'83a380000000fb');
 inputs.push({stage,phase:'Timeline',readyNs:timeline.hostMonotonicNs,completionSource:timelineWrite?'original43605aAfterLoadingFlagClear':'firstObservedClearMainResourceBoundary',boundedByFirstObservedClearControlFlag:!timelineWrite});
 assert.equal(c.observed_phase_events(stage,...inputs.map(x=>baseNow+BigInt(x.readyNs)-playerOrigin)),1);phaseInputs.push(...inputs);

}

let normalBoundary=null;
if(options.has('normal-boundary-observation')){
 assert(prefix>0&&schedulerPhases==='observed'&&!options.has('scene-copy-observation'));
 const proof=JSON.parse(read(resolve(root,options.get('normal-boundary-observation'))));
 assert(proof.verifiedControlledOriginalNormalAnmBoundary&&proof.diagnosticPrefixOnly&&!proof.ordinaryIndependentThreadTimingAcceptance);
 assert.equal(proof.verifierSha256,sha(read(resolve(root,'tools/th14-controlled-worker-boundary-evidence-oct29.py'))));
 for(const[path,row]of Object.entries(proof.bindings))assert.equal(sha(read(resolve(root,path))),row.sha256,'Changed controlled observation '+path);
 assert.equal(proof.bindings[relative(root,resolve(nativeHome,'report.json')).replaceAll('\\','/')]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
 assert(nativeReport.threadSchedulingControlled&&nativeReport.controlledScheduleComplete&&!nativeReport.hardwareBreakpointsOnly);
 const events=nativeReport.controlledScheduleEvents;
 assert.equal(events.length,4);assert.equal(events[0].pc,0x47e5e0);assert.equal(events[2].pc,0x456135);
 assert.equal(events[0].precedingPlayerCallbacks,proof.precedingPlayerCallbacks);
 normalBoundary={callback:proof.precedingPlayerCallbacks,readyNs:events[2].hostMonotonicNs,stage:proof.stage,originalPc:proof.originalMainHoldPc};
 assert.equal(c.observed_normal_clock(normalBoundary.callback,baseNow+BigInt(normalBoundary.readyNs)-playerOrigin),1);
}
let normalVmBoundary=null;
assert(!options.has('vm-boundary-baseline')||options.get('vm-boundary-baseline')==='true'&&options.has('normal-vm-boundary-observation'));
if(options.has('normal-vm-boundary-observation')){
 assert(prefix===33000&&schedulerPhases==='observed'&&!normalBoundary&&!options.has('scene-copy-observation'));
 const proof=JSON.parse(read(resolve(root,options.get('normal-vm-boundary-observation'))));
 assert(proof.verifiedControlledOriginalNormalVmReturnBoundary&&proof.diagnosticPrefixOnly&&!proof.ordinaryIndependentThreadTimingAcceptance);
 assert.equal(proof.verifierSha256,sha(read(resolve(root,'tools/th14-controlled-vm-worker-evidence-oct29.py'))));
 for(const[path,row]of Object.entries(proof.bindings))assert.equal(sha(read(resolve(root,path))),row.sha256,'Changed controlled VM observation '+path);
 assert.equal(proof.bindings[relative(root,resolve(nativeHome,'report.json')).replaceAll('\\','/')]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
 assert(nativeReport.threadSchedulingControlled&&nativeReport.controlledScheduleComplete&&!nativeReport.hardwareBreakpointsOnly);
 const events=nativeReport.controlledScheduleEvents;assert.equal(events.length,6);
 assert.equal(events[1].pc,0x47e660);assert.equal(events[4].pc,0x456135);
 normalVmBoundary={callback:proof.precedingPlayerCallbacks,readyNs:events[4].hostMonotonicNs,stage:proof.stage,originalPc:proof.originalMainReturnPc,file:proof.targetVmFile,script:proof.targetVmScript,retainedBaseline:options.has('vm-boundary-baseline')};
 assert.equal(c.observed_normal_vm_clock(normalVmBoundary.callback,baseNow+BigInt(normalVmBoundary.readyNs)-playerOrigin,normalVmBoundary.file,normalVmBoundary.script),1);
}

assert.equal(prefix,18000);assert.deepEqual(expectedSelection,[0,1,1,1]);
assert.equal(nativeReport.sourceFullReplaySha256,'c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74');assert.equal(schedulerPhases,'observed');
assert.equal(c.step_rng_session_install(2),1);
assert.equal(c.public_replay_clock(1/60),1);
let modeled=1,activeStage2Callbacks=0;
for(let i=1;i<limit;i++){
 lastNow=baseNow+times.readBigUInt64LE(i*8)-playerOrigin;
 let updateNow=lastNow;
 if(phasedScheduler&&maxStage>=2){
  const observed=controlClock.get(i+1)??pumpClock.get(i+1);if(observed!==undefined)updateNow=baseNow+BigInt(observed)-playerOrigin;
  const nextCamera=sceneNextCameraClock.get(i+1);if(nextCamera!==undefined){const boundary=baseNow+BigInt(nextCamera)-playerOrigin;if(updateNow<boundary)updateNow=boundary;}
  assert(updateNow<=lastNow);assert.equal(c.observed_player_boundary(i+1,lastNow),1);
 }
 assert.equal(c.menu_tick(updateNow,0),1,'Production GameSession tick failed');
 if(phasedScheduler&&maxStage>=2)assert.equal(c.observed_boundary_ok(),1);
 const beforeDraw=beforeDrawWorker.get(i+1);if(beforeDraw!==undefined)assert.equal(c.observed_worker_boundary(baseNow+BigInt(beforeDraw)-playerOrigin),1);
 assert.equal(c.draw(),1);c.probe_retire_capture();
 const afterDraw=afterDrawWorker.get(i+1);if(afterDraw!==undefined)assert.equal(c.observed_worker_boundary(baseNow+BigInt(afterDraw)-playerOrigin),1);
 assert.equal(c.public_replay_clock((i+1)/60),1);assert.equal(c.public_replay_observations(),i+1);modeled=i+1;
 const state=new Uint32Array(c.memory.buffer,c.reference_data(),32);
 if(state[30]===2&&state[0]>0&&c.step_rng_session_value(3,4)===0)++activeStage2Callbacks;
 assert.equal(c.menu_state(0),1,'Controlled prefix left the live stage unexpectedly');
 if(activeStage2Callbacks>=64)break;
}
const rngEvents=Array.from({length:c.step_rng_session_value(3,0)},(_,i)=>Array.from({length:12},(_,k)=>c.step_rng_session_value(i,k)>>>0));
assert.equal(rngEvents.length,3);assert.deepEqual(rngEvents.map(row=>row[0]),[0,2,3]);
assert(rngEvents.every(row=>row[2]===2&&row[3]===2&&row[10]===1&&row[11]===0));
assert(rngEvents[1][1]>=rngEvents[0][1]+2&&rngEvents[2][1]>=rngEvents[1][1]+2);
assert.equal(rngEvents[0][4],rngEvents[0][8]);assert.equal(rngEvents[1][6],rngEvents[1][8]);assert.equal(rngEvents[2][5],0);
assert.equal(c.step_rng_session_value(3,1),0);assert.equal(c.step_rng_session_value(3,2),0);
assert.equal(c.step_rng_session_value(3,3),1);assert.equal(c.step_rng_session_value(3,4),0);
assert.equal(activeStage2Callbacks,64);assert.equal(c.step_rng_session_finish(),1);
const summary={verifiedControlledProductionSessionRngResume:true,modeledCallbacks:modeled,activeStage2Callbacks,
 events:rngEvents,explicitlyControlledReadiness:true,minimumPlayerCallbacksBetweenStores:2,
 earlyHudSceneOrTimelineRequests:false,actualGameSessionBattleAndStagedLoader:true,
 nativeValuesProvidedToEngine:false,originalCapturedScheduleEquivalenceAccepted:false,
 oldRngOrBulletFailuresClosed:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,
 wasmSha256:sha(wasm),driverSha256:sha(read(import.meta.filename))};
write(resolve(out,'step-session.json'),JSON.stringify(summary,null,2)+'\n');console.log(JSON.stringify(summary));
