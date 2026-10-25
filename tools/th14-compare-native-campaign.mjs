import{gunzipSync}from'node:zlib';
import assert from'node:assert/strict';import{readFileSync as read,writeFileSync as write,mkdirSync as mkdir,existsSync as exists}from'node:fs';
import{resolve,dirname,basename,relative,isAbsolute}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
// Explicit case inputs; no native gameplay state is supplied to the engine.
const allowed=new Set(['native','assets','build','wasm','output','prefix','selection','hud-ready','publication-cutoff']);
const options=new Map();for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i]?.replace(/^--/,'');assert(allowed.has(key)&&process.argv[i+1]&&!options.has(key),'Unknown, repeated or missing option '+key);options.set(key,process.argv[i+1]);}
for(const key of ['native','assets','build','output','selection'])assert(options.has(key),'Missing --'+key);
const root=resolve(import.meta.dirname,'..'),nativeHome=resolve(root,options.get('native')),nativeName=basename(nativeHome),mode='initial-worker-events',home=dirname(resolve(root,options.get('build')));
const sha=b=>createHash('sha256').update(b).digest('hex'),prefix=Number(options.get('prefix')??0),publicationCutoff=Number(options.get('publication-cutoff')??1000),expectedSelection=options.get('selection').split(',').map(Number),hudFlag=(options.get('hud-ready')??'cpu-write')==='cpu-write'?'-cpu-write':'-main-resource-boundary';
assert(Number.isInteger(prefix)&&prefix>=0&&Number.isInteger(publicationCutoff)&&publicationCutoff>0);
assert(expectedSelection.length===4&&expectedSelection.every(Number.isInteger));assert(['cpu-write','boundary'].includes(options.get('hud-ready')??'cpu-write'));
const out=resolve(root,options.get('output')),scope=relative(resolve(root,'artifacts/th14'),out);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope),'New TH14 artifact directory required');
const nativeReport=exists(resolve(nativeHome,'report.json'))?JSON.parse(read(resolve(nativeHome,'report.json'))):null,initial=JSON.parse(read(resolve(nativeHome,'untouched-first-player.json')));
if(nativeReport)assert.equal(nativeReport.anmPublicationTraceCutoffPlayerCallbacks,publicationCutoff,'Declared publication cutoff differs from capture');
const progress=nativeReport??JSON.parse(read(resolve(nativeHome,'progress.json'))),limit=prefix||nativeReport?.callbacks;assert(limit&&progress.callbacks>=limit);assert.deepEqual(initial.words.slice(27,31),expectedSelection);
if(!prefix){assert(nativeReport.observedForcedReplayEndMenu&&nativeReport.childExited&&!nativeReport.error&&nativeReport.gameStateWordWrites===1&&!nativeReport.rngOrCounterWrites);assert(nativeReport.caseInitialization.attractBitClearOnly);assert(nativeReport.caseInitialization.beforeFlags&0x40);assert.equal(nativeReport.caseInitialization.afterFlags,nativeReport.caseInitialization.beforeFlags&~0x40);}
const events=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x)).filter(x=>x.hostMonotonicNs<=initial.hostMonotonicNs),frames=events.filter(x=>x.event==='main-resource-pump'),native=read(resolve(nativeHome,'allocation-events.jsonl'),'utf8').trim().split('\n').map(x=>JSON.parse(x));
const flags=['signature-ready-flag-published','ascii-ready-flag-published'].map(k=>events.find(x=>x.event===k));assert(flags.every(Boolean));
const origin=BigInt(frames[0].hostMonotonicNs);assert(!exists(out));mkdir(out,{recursive:true});
const wasm=read(resolve(root,options.get('wasm')??resolve(home,'observer.wasm'))),build=JSON.parse(read(resolve(root,options.get('build'))));assert.equal(sha(wasm),build.wasmSha256);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
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
for(let stage=2;stage<=maxStage;stage++){
 const call=transition.find(x=>x.event==='sleep60-before-call'&&x.stage===stage),returned=transition.find(x=>x.event==='sleep60-returned'&&x.stage===stage);assert(call&&returned&&returned.returnInstructionObservedDirectly);
 assert.equal(c.observed_worker_events(stage,baseNow+BigInt(call.hostMonotonicNs)-playerOrigin,baseNow+BigInt(returned.hostMonotonicNs)-playerOrigin),1);
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
  inputs.push({stage,phase,file,queuedNs:queued?.hostMonotonicNs??null,queueObservedDirectly:!!queued,resourceFirstObservedNs:firstObserved?.hostMonotonicNs??null,readyNs,completionSource,boundedByFirstObservedReadyMainBoundary:completionSource==='firstObservedResourceReadyMainBoundary'});
 }
 const timelineWrite=later.find(x=>x.event==='initial-control-loading-flag-cleared'&&x.stage===stage&&x.observedOriginalLoadingFlagClear);
 const timeline=timelineWrite??frames.find(x=>!(x.controlFlags&4));assert(timeline,'Missing Timeline ready '+stage);
 if(timelineWrite)assert.equal(timelineWrite.clearInstructionBytes,'83a380000000fb');
 inputs.push({stage,phase:'Timeline',readyNs:timeline.hostMonotonicNs,completionSource:timelineWrite?'original43605aAfterLoadingFlagClear':'firstObservedClearMainResourceBoundary',boundedByFirstObservedClearControlFlag:!timelineWrite});
 assert.equal(c.observed_phase_events(stage,...inputs.map(x=>baseNow+BigInt(x.readyNs)-playerOrigin)),1);phaseInputs.push(...inputs);

}

const combatSnapshots=[],combatDifferences=[],nativeCombatIndex=JSON.parse(read(resolve(nativeHome,'combat-pool-index.json'))),nativeCombatByCallback=new Map(nativeCombatIndex.snapshots.map(x=>[x.callback,x]));
function compare(index){
 const mask=c.bullet_skipped_mask()>>>0,nativeMask=c.bullet_unsupported_native_mask()>>>0;if(mask!==unsupportedMask||nativeMask!==unsupportedNativeMask){unsupportedObservations.push({index,mask,nativeMask});unsupportedMask=mask;unsupportedNativeMask=nativeMask;}

 if(c.combat_meta(0)===index+1){
  const names=['enemies','bullets','shots','areas','items','lasers'],strides=[31,18,19,19,13,26],rows={};
  for(let k=0;k<6;k++){const size=c.combat_size(k);assert.equal(size%strides[k],0);const flat=Array.from(new Uint32Array(c.memory.buffer,c.combat_data(k),size));rows[names[k]]=Array.from({length:size/strides[k]},(_,r)=>flat.slice(r*strides[k],(r+1)*strides[k]));}
  const snapshot={callback:c.combat_meta(0),stage:c.combat_meta(1),stageFrame:c.combat_meta(2),rows,readOnly:true,completeGame:false,nativeEquivalent:false};
  write(resolve(out,'combat-'+snapshot.callback+'.json'),JSON.stringify(snapshot)+'\n',{flag:'wx'});
  const binding=nativeCombatByCallback.get(snapshot.callback);assert(binding,'Missing native checkpoint '+snapshot.callback);
  const compressed=read(resolve(nativeHome,'combat-pools',binding.file));assert.equal(sha(compressed),binding.sha256);
  const original=JSON.parse(gunzipSync(compressed));assert.equal(original.callback,snapshot.callback);assert.equal(original.stage,snapshot.stage);assert.equal(original.stageFrame,snapshot.stageFrame);
  const semanticSchema={"enemies": [["instance", 4580], ["health", 20836], ["maxHealth", 20840], ["score", 20832], ["flags", 21060], ["current.x", 4660], ["current.y", 4664], ["current.z", 4668], ["current.vx", 4712], ["current.vy", 4716], ["current.vz", 4720], ["absolute.x", 4728], ["absolute.y", 4732], ["absolute.z", 4736], ["absolute.vx", 4780], ["absolute.vy", 4784], ["absolute.vz", 4788], ["relative.x", 4796], ["relative.y", 4800], ["relative.z", 4804], ["relative.vx", 4848], ["relative.vy", 4852], ["relative.vz", 4856], ["current.speed", 4684], ["current.angle", 4688], ["absolute.speed", 4752], ["absolute.angle", 4756], ["relative.speed", 4820], ["relative.angle", 4824], ["immunity", 20960], ["timer2bc", 5296]], "bullets": [["state", 3086], ["flags", 32], ["collisionDelay", 36], ["x", 3008], ["y", 3012], ["z", 3016], ["vx", 3020], ["vy", 3024], ["vz", 3028], ["speed", 3032], ["angle", 3036], ["hitboxX", 3040], ["hitboxY", 3044], ["lifetime", 5060], ["spriteColor", 5100], ["activeTransforms", 3076], ["sizeCurrent", 5020], ["size", 5052]], "shots": [["slot", null], ["state", 152], ["timerPrevious", 24], ["timerCurrent", 28], ["timerFraction", 32], ["flags", 16], ["animation", 20], ["x", 84], ["y", 88], ["z", 92], ["speed", 108], ["angle", 112], ["vx", 136], ["vy", 140], ["vz", 144], ["collisionWidth", 176], ["damage", 172], ["hitThis", 164], ["hitLast", 168]], "areas": [["slot", null], ["flags", 16], ["radius", 20], ["angle", 28], ["width", 36], ["height", 40], ["x", 44], ["y", 48], ["z", 52], ["timerPrevious", 112], ["timerCurrent", 116], ["timerFraction", 120], ["growth", 24], ["angularVelocity", 32], ["damage", 132], ["total", 136], ["maximum", 140], ["period", 144], ["stamp", 148]], "items": [["slot", null], ["state", 3056], ["type", 3060], ["displayType", 3064], ["x", 2988], ["y", 2992], ["z", 2996], ["vx", 3000], ["vy", 3004], ["vz", 3008], ["lifetimeFraction", 3024], ["attractionSpeed", 3068], ["delay", 3072]], "lasers": [["id", 128], ["type", 20], ["state", 16], ["lifetimePrevious", 24], ["lifetimeCurrent", 28], ["lifetimeFraction", 32], ["grazePrevious", 44], ["grazeCurrent", 48], ["grazeFraction", 52], ["x", 84], ["y", 88], ["z", 92], ["vx", 96], ["vy", 100], ["vz", 104], ["angle", 108], ["length", 112], ["width", 116], ["speed", 120], ["offset", 124], ["transformIndex", 1428], ["activeTransforms", 1432], ["offscreenPrevious", 1440], ["offscreenCurrent", 1444], ["offscreenFraction", 1448], ["protection", 1460]]};
  for(const name of names){const p=rows[name],fields=semanticSchema[name],n=original.original[name].map(object=>{const raw=Buffer.from(object.rawHex,'hex');return fields.map(([field,offset])=>offset===null?object.slot:name==='bullets'&&field==='state'?raw.readUInt16LE(offset):raw.readUInt32LE(offset));});
   if(p.length!==n.length)combatDifferences.push({callback:snapshot.callback,stage:snapshot.stage,stageFrame:snapshot.stageFrame,family:name,kind:'poolCount',native:n.length,portable:p.length});
   for(let row=0;row<Math.min(p.length,n.length);row++){assert.equal(p[row].length,fields.length);assert.equal(n[row].length,fields.length);for(let k=0;k<fields.length;k++)if(p[row][k]!==n[row][k])combatDifferences.push({callback:snapshot.callback,stage:snapshot.stage,stageFrame:snapshot.stageFrame,family:name,row,field:fields[k][0],native:n[row][k],portable:p[row][k]});}
  }
combatSnapshots.push({callback:snapshot.callback,stage:snapshot.stage,stageFrame:snapshot.stageFrame,counts:Object.fromEntries(names.map(n=>[n,rows[n].length]))});
 }

 const hw=Array.from({length:2},(_,k)=>c.observed_hud_word(k)>>>0);hudRows.push(...hw);for(let k=0;k<2;k++){const n=hudRaw.readUInt32LE(index*8+k*4);if(n!==hw[k]){hudCounts[k]=(hudCounts[k]??0)+1;hudFirst[k]??={index,stage:nativeRaw.readUInt32LE(index*128+30*4),stageFrame:nativeRaw.readUInt32LE(index*128),field:k,native:n,portable:hw[k]};}}
 if(index+1===75000)lateStartCount=c.observed_creation_count();if(index+1===Math.min(limit,91000))lateEndCount=c.observed_creation_count();
 const cw=Array.from({length:25},(_,k)=>c.observed_camera_word(k)>>>0);cameraRows.push(...cw);
 for(let k=0;k<25;k++){const native=cameraRaw.readUInt32LE(index*0x124+cameraOffsets[k]);if(native!==cw[k]){cameraCounts[k]=(cameraCounts[k]??0)+1;cameraFirst[k]??={index,field:k,native,portable:cw[k]};}}
 if(index+1===Math.min(limit,publicationCutoff))allocationBoundaryCount=c.observed_creation_count();collect(index+1);const row=Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32));rows.push(...row);for(let k=0;k<32;k++){const n=nativeRaw.readUInt32LE(index*128+k*4);if(n===row[k])continue;counts[k]=(counts[k]??0)+1;const d={index,stage:row[30],stageFrame:row[0],word:k,native:n,portable:row[k]};first[k]??=d;firstDifference??=d;}}
initialCreationCount=c.observed_creation_count();compare(0);assert.equal(c.public_replay_clock(1/60),1);let end=null;
for(let i=1;i<limit;i++){
 lastNow=baseNow+times.readBigUInt64LE(i*8)-playerOrigin;
 assert.equal(c.menu_tick(lastNow,0),1);assert.equal(c.draw(),1);c.probe_retire_capture();assert.equal(c.public_replay_clock((i+1)/60),1);
 assert.equal(c.public_replay_observations(),i+1);compare(i);
 if(c.menu_state(0)!==1){end={index:i,state:Array.from({length:20},(_,n)=>c.menu_state(n))};break;}
 if((i+1)%3000===0)console.log(JSON.stringify({callbacks:i+1,differenceCounts:counts}));
}
const sampled=c.public_replay_observations();
for(let i=1;i<=600&&!end&&!prefix;i++){
 const now=lastNow+BigInt(i)*1000000000n/60n;assert.equal(c.menu_tick(now,0),1);assert.equal(c.draw(),1);c.probe_retire_capture();assert.equal(c.public_replay_clock((sampled+i)/60),1);
 if(c.menu_state(0)!==1){end={tailTicks:i,now:String(now),state:Array.from({length:20},(_,n)=>c.menu_state(n))};lastNow=now;break;}
}
let stable=null;if(end&&!prefix){for(let i=1;i<=90;i++){const now=lastNow+BigInt(i)*1000000000n/60n;assert.equal(c.menu_tick(now,0),1);assert.equal(c.draw(),1);c.probe_retire_capture();assert.equal(c.public_replay_clock((sampled+i)/60),1);}stable=Array.from({length:20},(_,n)=>c.menu_state(n));}
const raw=Buffer.from(new Uint32Array(rows).buffer);write(resolve(out,'selected-state.u32'),raw,{flag:'wx'});
const report={comparisonToolSha256:sha(read(new URL(import.meta.url))),declaredSelection:expectedSelection,publicationCutoff,portableUnsupportedBulletObservations:unsupportedObservations,allPortableBulletOpcodesSupported:unsupportedObservations.length===0,diagnosticPrefixOnly:!!prefix,nativeCaptureMayStillBeRunning:!nativeReport,observedPhaseInputs:phaseInputs,completed:true,derivedSingleStageReplay:false,intactOriginalReplay:true,selection:initial.words.slice(27,31),stageHeaderInputAndFpsRetainedExactly:true,sourceReplaySha256:assetManifest.replaySha256,archiveSha256:sha(archive),replayBytesSha256:sha(replayBytes),callbacks:rows.length/32,nativeCallbacks:progress.callbacks,selectedSha256:sha(raw),nativeSelectedSha256:sha(nativeRaw),allRaw32ByteIdentical:raw.equals(nativeRaw),differenceCounts:counts,firstDifferences:first,firstDifference,entry,end,stableMenuAfter90Ticks:stable,finalObservedCallbacks:c.public_replay_observations(),nativeInitialSnapshotSha256:sha(read(resolve(nativeHome,'untouched-first-player.json'))),nativeResourceEventsSha256:sha(read(resolve(nativeHome,'resource-ready-events.jsonl'))),nativeTimesSha256:sha(times),wasmSha256:sha(wasm),actualInitialTimeGetTime:initial.actualInitialTimeGetTimeInput,actualCookie:initial.actualOriginalSecurityCookie,declaredGeometryFrame:0x1aec84,observedNativeHostTimes:true,extraAsciiDrawBeginBoundaryTimestamp:asciiBegin.hostMonotonicNs,asciiBeginDeliveryInferredFromFirstPublication:false,asciiCreateObservedAtOriginal44477aCall:true,asciiDeliveryResult,noNativePublicationValuesProvidedToEngine:true,declaredAttractBitClearAtFirstPlayer:true,noRngSerialCounterHealthOrInputWrites:true,noPerFrameStateOverrides:true,recordingGraphics:true,actualGpuOrAudio:false,completeGame:false,nativeEquivalent:false};
write(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));
assert.equal(report.callbacks,limit);assert.equal(report.finalObservedCallbacks,limit);if(!prefix){assert(end);assert.equal(stable[0],2);assert.equal(stable[5],3);}

const rawOffsets=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,...Array.from({length:8},(_,i)=>0x3b8+i*4),...Array.from({length:8},(_,i)=>0x4ac+i*4)];
const extraFields=['visible','drawingMode',...rawOffsets.map(x=>'nativeVmWord0x'+x.toString(16)),'scriptInstructionOffset','worldX','worldY','worldZ','vertexColorMode','blendMode','depthDisabled','flipX','flipY','anchorX','anchorY','addressV','cameraFollow','extraFloat0','extraFloat1','extraFloat2','extraInt0','extraInt1','randomScale0','randomScale1','randomBound','scaleVelocityX','scaleVelocityY'],fields=['handle','file','script','timerPrevious','timerCurrent','timerFraction','pendingInterrupt','ageCurrent',...extraFields];assert.equal(fields.length,80);
const interpDefinitions=[['position',0x9c,3],['color',0xf4,3],['alpha',0x14c,1],['rotation',0x17c,3],['scale',0x204,2],['color2',0x2d0,3],['alpha2',0x328,1],['scrollX',0x358,1],['scrollY',0x388,1],['extraScale',0x248,2],['textureScale',0x28c,2]];
for(const[name,base,n]of interpDefinitions){for(const group of ['start','end','initialTangent','finalTangent'])for(let i=0;i<n;i++)fields.push(name+'.'+group+i);for(const field of ['timerPrevious','timerCurrent','timerFraction','timerFlags','duration','mode'])fields.push(name+'.'+field);}
assert.equal(fields.length,234);
const transformFields=['childX','childY','childZ','pivotX','pivotY','slowdown','parentHandle','timerFlags','ageFlags',...['spriteMatrix','transformMatrix','uvMatrix'].flatMap(x=>Array.from({length:16},(_,i)=>x+i))];fields.push(...transformFields);assert.equal(fields.length,291);const linkFields=['registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle'];fields.push(...linkFields);assert.equal(fields.length,295);const interruptFields=['savedTimerPrevious','savedTimerCurrent','savedTimerFraction','savedTimerRatePresent','savedTimerFlags','savedInstructionOffset','spriteFrame','inheritedColorCache'];fields.push(...interruptFields);assert.equal(fields.length,303);
const snapshots=[];
for(const [at,frame]of[1,26000,30000,36000,38900,60000,90000,120000].entries()){
 if(frame>limit)continue;const np=resolve(nativeHome,'live-vms-callback-'+frame+'.json');assert(exists(np));const nr=JSON.parse(read(np));const nativeHandleByAddress=new Map(nr.rows.map(x=>[Buffer.from(x.rawVmHex,'hex').readUInt32LE(0x570),x.handle]));
 const pr=Array.from({length:c.mid_count(at)},(_,r)=>Array.from({length:303},(_,k)=>c.mid_value(at,r,k)>>>0)),byId=new Map(pr.map(x=>[x[0],x])),nativeIds=new Set(nr.rows.map(x=>x.handle)),differences=[];
 for(const n of nr.rows){const raw=Buffer.from(n.rawVmHex,'hex'),flags=raw.readUInt32LE(0x18),values=[flags&1,(flags>>>25)&31,...rawOffsets.map(x=>raw.readUInt32LE(x)),raw.readUInt32LE(0x28)?(raw.readUInt32LE(0x28)-raw.readUInt32LE(0x38))>>>0:0xffffffff,...[0x59c,0x5a0,0x5a4].map(x=>raw.readUInt32LE(x)),(flags>>>17)&3,(flags>>>5)&15,Number(!!(flags&0x2000)),Number(!!(flags&0x800)),Number(!!(flags&0x1000)),(flags>>>21)&3,(flags>>>23)&3,flags>>>30,Number(!!(flags&0x8000)),...[0x4cc,0x4d0,0x4d4,0x4d8,0x4dc,0x4e0,0x4e4,0x4e8,0x70,0x74].map(x=>raw.readUInt32LE(x))];for(let k=0;k<extraFields.length;k++)n[extraFields[k]]=values[k];for(const[name,base,nc]of interpDefinitions){const offsets=[...Array.from({length:4*nc},(_,i)=>base+i*4),...[0,4,8,16,20,24].map(x=>base+5*nc*4+x)];let start=fields.indexOf(name+'.start0');for(const off of offsets)n[fields[start++]]=raw.readUInt32LE(off);}
const parentAddress=raw.readUInt32LE(0x594);assert(!parentAddress||nativeHandleByAddress.has(parentAddress),'parent absent from live registry');
const transformValues=[...[0x4ec,0x4f0,0x4f4,0x90,0x94,0x598].map(x=>raw.readUInt32LE(x)),parentAddress?nativeHandleByAddress.get(parentAddress):0,raw.readUInt32LE(0x558),raw.readUInt32LE(0x56c),...Array.from({length:48},(_,i)=>raw.readUInt32LE(0x3e0+i*4))];transformFields.forEach((k,i)=>n[k]=transformValues[i]);for(const[k,off]of[0x574,0x578,0x584,0x588].entries()){const p=raw.readUInt32LE(off),address=p-(k<2?0x570:0x580);assert(!p||nativeHandleByAddress.has(address),'Native neighbor absent from live registry');n[linkFields[k]]=p?nativeHandleByAddress.get(address):0;}
const interruptValues=[raw.readUInt32LE(0),raw.readUInt32LE(4),raw.readUInt32LE(8),Number(raw.readUInt32LE(12)!==0),raw.readUInt32LE(16),raw.readUInt32LE(20)?(raw.readUInt32LE(20)-raw.readUInt32LE(0x38))>>>0:0xffffffff,raw.readUInt32LE(0x4a4),raw.readUInt32LE(0x53c)];interruptFields.forEach((key,i)=>n[key]=interruptValues[i]);const p=byId.get(n.handle);if(!p){differences.push({handle:n.handle,missingInPortable:true,file:n.file,script:n.script});continue;}for(let k=0;k<fields.length;k++)if(n[fields[k]]!==p[k])differences.push({handle:n.handle,file:n.file,script:n.script,field:fields[k],native:n[fields[k]],portable:p[k]});}
 for(const p of pr)if(!nativeIds.has(p[0]))differences.push({handle:p[0],extraInPortable:true,file:p[1],script:p[2]});
 const registryOrderEqual=nr.rows.length===pr.length&&nr.rows.every((x,i)=>x.handle===pr[i][0]);const record={registryOrderEqual,frame,nativeCount:nr.rows.length,portableCount:pr.length,portableExpected:c.mid_expected(at),portableRegistryComplete:!!c.mid_complete(at),differenceCount:differences.length,differences};snapshots.push(record);write(resolve(out,'portable-live-'+frame+'.json'),JSON.stringify(pr)+'\n');
}
const liveReport={completed:true,prefixSelected32ByteIdentical:report.allRaw32ByteIdentical,comparedValues:303,fields,snapshots,allLiveValuesEqual:snapshots.every(x=>x.portableRegistryComplete&&x.registryOrderEqual&&!x.differenceCount),diagnosticPrefixOnly:!!prefix,wasmSha256:sha(wasm),actualGpuOrAudio:false,completeGame:false,nativeEquivalent:false};write(resolve(out,'live-report.json'),JSON.stringify(liveReport,null,2)+'\n');console.log(JSON.stringify({allLiveValuesEqual:liveReport.allLiveValuesEqual,snapshots:snapshots.map(({differences,...r})=>r),firstDifferences:snapshots.map(x=>({frame:x.frame,differences:x.differences.slice(0,5)}))}));


const portableCamera=Buffer.from(new Uint32Array(cameraRows).buffer);write(resolve(out,'portable-camera.u32'),portableCamera,{flag:'wx'});write(resolve(out,'native-camera.raw'),cameraRaw,{flag:'wx'});
const cameraReport={completed:true,callbacks:limit,selectedCameraFields:25,offsets:cameraOffsets,counts:cameraCounts,first:cameraFirst,portableSha256:sha(portableCamera),nativeSha256:sha(cameraRaw),wasmSha256:sha(wasm),allCameraWordsEqual:Object.keys(cameraCounts).length===0,completeGame:false,nativeEquivalent:false};write(resolve(out,'camera-report.json'),JSON.stringify(cameraReport,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(cameraReport));
const portableHud=Buffer.from(new Uint32Array(hudRows).buffer);write(resolve(out,'portable-hud.u32'),portableHud,{flag:'wx'});write(resolve(out,'native-hud.u32'),hudRaw,{flag:'wx'});
const hudReport={completed:true,callbacks:limit,fields:['HUD displayed score units','global internal score units'],nativeOffsets:['[0x4db550]+0x140','0x4f5830'],differenceCounts:hudCounts,firstDifferences:hudFirst,allHudWordsEqual:portableHud.equals(hudRaw),portableSha256:sha(portableHud),nativeSha256:sha(hudRaw),terminalPortable:[c.current_hud_word(0)>>>0,c.current_hud_word(1)>>>0],terminalNative:nativeReport?.terminalMenuSamples??null,wasmSha256:sha(wasm),readOnly:true,completeGame:false,nativeEquivalent:false};write(resolve(out,'hud-report.json'),JSON.stringify(hudReport,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(hudReport));
const windows=[{name:'initial-through-'+Math.min(limit,publicationCutoff),fromCount:0,toCount:allocationBoundaryCount,nativeRows:native.filter(x=>x.precedingPlayerCallbacks<Math.min(limit,publicationCutoff))}];
const allocationReports=[];for(const window of windows){const portablePrefix=portable.filter(x=>x.creationIndex>window.fromCount&&x.creationIndex<=window.toCount).sort((a,b)=>a.publicationOrdinal-b.publicationOrdinal),nativePrefix=window.nativeRows;let firstHandle=null,firstIdentity=null;const paired=Math.min(nativePrefix.length,portablePrefix.length);for(let i=0;i<paired;i++){const n=nativePrefix[i],p=portablePrefix[i];if(!firstHandle&&n.handle!==p.handle)firstHandle={index:i,native:n,portable:p};if(!firstIdentity&&(n.file!==p.file||n.script!==p.script))firstIdentity={index:i,native:n,portable:p};}const ar={window:window.name,nativeCount:nativePrefix.length,portableCount:portablePrefix.length,paired,firstHandleDifference:firstHandle,firstIdentityDifference:firstIdentity,allHandlesFileScriptEqual:nativePrefix.length===portablePrefix.length&&!firstHandle&&!firstIdentity,portableCreationRange:[window.fromCount,window.toCount]};allocationReports.push(ar);write(resolve(out,'portable-allocations-'+window.name+'.json'),JSON.stringify(portablePrefix)+'\n',{flag:'wx'});}
const allocationReport={completed:true,windows:allocationReports,nativeTraceCutoffCallbacks:publicationCutoff,scope:'Compare only untouched boot and declared initial publication window; no claim about later allocations. All original handle-slot differences are retained.',completeGame:false,nativeEquivalent:false};write(resolve(out,'allocation-report.json'),JSON.stringify(allocationReport,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(allocationReport));


write(resolve(out,'combat-snapshots.json'),JSON.stringify({snapshots:combatSnapshots,nativeCombatComparisonPerformed:true,allNativeSelectedFieldsRecomputedFromRetainedRawBytes:true,semanticSchemaVersion:3,publicationOrderUsesUnwrappedCounterWithoutNativeValues:true,differences:combatDifferences,allCapturedCombatWordsEqual:combatDifferences.length===0,completeGame:false,nativeEquivalent:false},null,2)+'\n');

console.log(JSON.stringify({combatCheckpoints:combatSnapshots.length,combatDifferenceCount:combatDifferences.length,firstCombatDifferences:combatDifferences.slice(0,10)}));if(combatDifferences.length)process.exitCode=1;

console.log(JSON.stringify({allPortableBulletOpcodesSupported:unsupportedObservations.length===0,unsupportedObservations}));if(unsupportedObservations.length)process.exitCode=1;

assert(report.allRaw32ByteIdentical);
