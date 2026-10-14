// Independent private integrated playback; injected60Hz clock is controlled,
// never an invented Native worker duration. All callback differences retained.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),revision=process.env.TH14_STAGED_REVISION||'',home=resolve(root,'artifacts/th14/staged-loader-integration-oct14',revision||'.'),rt=resolve(home,revision?'source/runtimes/th12/th12_web':'private/runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const replayPath=resolve(root,process.argv[2]||'artifacts/th14/public-replay-reference/th14_udzp01.rpy'),label=process.argv[3]||'reimua-lunatic-controlled-v1';assert(/^[a-z0-9-]{1,64}$/.test(label));
const out=resolve(home,'playback',label);assert(!existsSync(resolve(out,'report.json')),'Choose a new immutable result label');mkdirSync(out,{recursive:true});
const buildBytes=readFileSync(resolve(home,'private-build.json')),build=JSON.parse(buildBytes),wasmBytes=readFileSync(resolve(home,'staged-loader-integration.wasm'));assert.equal(sha(wasmBytes),build.wasmSha256);
for(const [p,h] of Object.entries(build.privateSourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,p);
const fixture=resolve(rt,'tests/cpp/th14-staged-loader-integration-fixture.cpp');assert.equal(sha(readFileSync(fixture)),build.fixtureSha256);
const replay=readFileSync(replayPath),sourceBytes=readFileSync(replayPath.replace(/\.rpy$/,'-source.json')),replaySource=JSON.parse(sourceBytes);assert.equal(sha(replay),replaySource.sha256);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;},words=(method,n)=>{const p=c[method]();return Array.from(new Uint32Array(c.memory.buffer,p,n));};
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.integration_begin(upload(replay),replay.length),1);
const rows=[],active=[],loadingRows=[],transitions=[];let error='',frames=0,previousStage=c.public_replay_status(0),previousObservations=c.public_replay_observations();
const limit=+(process.argv[4]||200000);
for(let frame=1;frame<=limit;++frame){
 c.integration_clock(BigInt(frame)*1000000000n/60n);
 if(!c.tick(0)){error=text(c.error());break;}
 if(!c.draw()){error=text(c.error());break;}
 if(!c.public_replay_clock(frame/60)){error='Private spell clock failed';break;}frames=frame;
 const count=c.public_replay_observations(),stage=c.public_replay_status(0);
 assert(count===previousObservations||count===previousObservations+1,'A fresh physical before-player callback cannot be missed or reused');
 if(count===previousObservations+1){const isActive=c.public_replay_observed_active();rows.push(...words('reference_data',32));active.push(isActive);const state=words('integration_state',20);if(!isActive)loadingRows.push({frame,callback:count,clockNs:(BigInt(frame)*1000000000n/60n).toString(),state});}
 previousObservations=count;
 if(stage!==previousStage){const row={frame,from:previousStage,to:stage,state:words('integration_state',20)};transitions.push(row);console.log('Private actual resource transition',JSON.stringify(row));previousStage=stage;}
 if(c.phase()===3||c.phase()===4||c.phase()===5)break;
}
const states=Buffer.from(new Uint32Array(rows).buffer),activeBytes=Buffer.from(active);writeFileSync(resolve(out,'selected-state.u32'),states);writeFileSync(resolve(out,'callback-active.u8'),activeBytes);
const phaseCount=c.integration_phase_event_count(),phaseEvents=words('integration_phase_events',phaseCount*15),phaseRecords=Array.from({length:phaseCount},(_,i)=>phaseEvents.slice(i*15,i*15+15));
const semanticChecks=[];
for(let i=0;i<phaseRecords.length;i+=3){const [hud,scene,timeline]=phaseRecords.slice(i,i+3);if(!timeline){semanticChecks.push({complete:false,records:phaseRecords.slice(i)});break;}
 semanticChecks.push({stage:hud[0],complete:true,actualOrder:[hud[1],scene[1],timeline[1]],ownerBeforeHud:hud[4],ownerBeforeScene:scene[4],ownerBeforeTimelineUpload:timeline[4],nextIdBeforeTimelineUpload:timeline[5],timelineBoundBeforeUpload:timeline[6],parsedDefinitions:timeline[7],sceneObjects:scene[8],sceneInstructions:scene[9],parsedBackgroundScripts:scene[10],parsedLogoScripts:hud[11],actualStageConstructedBeforeTimeline:timeline[12],outgoingStageStillPresent:timeline[13],resultTimerAtHud:hud[14]});
}
let nativeComparison=null;
if(replayPath.endsWith('th14_udzp01.rpy')){
 const nativePath=resolve(root,'artifacts/th14/custom-replay-reference/zps-reimua-lunatic-full-template-layer-oct14/native-state.u32'),native=readFileSync(nativePath);
 assert.equal(sha(native),'488d9c4e03a817b6532b2ded28b7fe412c1898b62eddb788f63f9b571f89e5b0');
 const differences=[],perField={},perActiveField={},perInactiveField={};let callbacks=Math.min(native.length/128,rows.length/32);
 for(let row=0;row<callbacks;++row)for(let field=0;field<32;++field){const actual=rows[row*32+field],expected=native.readUInt32LE((row*32+field)*4);if(actual!==expected){differences.push(row+1,field,actual,expected);perField[field]=(perField[field]||0)+1;const map=active[row]?perActiveField:perInactiveField;map[field]=(map[field]||0)+1;}}
 const diffBytes=Buffer.from(new Uint32Array(differences).buffer);writeFileSync(resolve(out,'native-differences.u32'),diffBytes);
 nativeComparison={comparisonPassed:false,callbackCountsEqual:native.length/128===rows.length/32,nativeCallbacks:native.length/128,privateCallbacks:rows.length/32,comparedCallbacks:callbacks,wordDifferences:differences.length/4,perField,perActiveField,perInactiveField,nativeSha256:sha(native),allDifferencesRetained:true,differenceFileSha256:sha(diffBytes)};
}
const result={privatePrototype:true,productionChanged:false,productionVerified:false,nativeEquivalent:false,completeGame:false,frames,phase:c.phase(),stage:c.public_replay_status(0),error,candidatePlaybackEnded:!error&&c.phase()===4&&!c.public_replay_status(3),gameOverRequested:!!c.public_replay_status(3),selectedCallbacks:rows.length/32,inactiveCallbacks:active.filter(v=>!v).length,transitions,loadingCallbacks:loadingRows,resourcePhaseRecords:phaseRecords,semanticChecks,nativeComparison,clockMode:'controlled test clock floor(frame*1e9/60), explicitly injected via production-shaped clock callback; not captured Native scheduler time',gpuPrepared:false,captureQueueIntegrated:false,forceProgression:false,invulnerabilityOverride:false,sourceBuildSha256:sha(buildBytes),privateSourceHashes:build.privateSourceHashes,wasmSha256:sha(wasmBytes),fixtureSha256:sha(readFileSync(fixture)),replaySha256:sha(replay),replaySourceSha256:sha(sourceBytes),archiveSha256:sha(archive),selectedStateSha256:sha(states),callbackActiveSha256:sha(activeBytes),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Actual private GameSession/Battle next-stage path and original DAT resources. HUD/logo+selectedMSG, real STD/background/Stage construction, empty EnemyManager publication and real ECL/includes+ANM template preparation run in order, with outgoing Stage, Player and HUD callbacks retained. Clock is declared60Hz unit input; no Native wait-window constants. Headless StageResourceEffects use the existing no-GPU prepare_animation boundary; real template preparation is executed, GPU completion and first capture slot host integration remain absent. Every fresh before-player callback and every raw32 original difference retained. Candidate ending is no Native ordinary ending or1:1 claim.'};
writeFileSync(resolve(out,'report.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({privatePrototype:true,frames,phase:result.phase,stage:result.stage,error,ended:result.candidatePlaybackEnded,inactiveCallbacks:result.inactiveCallbacks,resourceEvents:phaseCount,nativeComparison}));
if(error||!result.candidatePlaybackEnded)process.exitCode=1;
