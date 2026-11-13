import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ordinary-difficulties-nov14');
const key=process.argv[2]??'reimua-normal',mode=process.argv[3]??'prefix';assert(['prefix','full'].includes(mode));assert(/^(reimu|marisa|sakuya)[ab]-(easy|normal|hard|lunatic)$/.test(key));
const inputHome=resolve(R,process.env.TH14_FLOW_INPUT_DIR??'artifacts/th14/royalflare-coverage-matrix-oct16/inputs'),inputMeta=JSON.parse(readFileSync(resolve(inputHome,key+'-source.json')));
const character=inputMeta.character,subtype=inputMeta.subtype,difficulty=inputMeta.difficulty,selection=character*2+subtype,expectedSeed=inputMeta.stages[0].seed;
const runName=process.env.TH14_FLOW_OUTPUT??key+'-'+mode+'-current';assert(/^[a-z0-9_-]+$/.test(runName));
const out=resolve(H,runName),component=resolve(R,process.env.TH14_FLOW_COMPONENT??'artifacts/th14/ordinary-difficulties-nov14/canonical-component');
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [n,h]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
const originalClock=initial.actualInitialTimeGetTimeInput;let startupSeed=expectedSeed;
for(let i=0;i<494;i++){const rotated=((startupSeed>>>2)|(startupSeed<<14))&65535;startupSeed=((rotated+0x6553)^0x9630)&65535;}
if(process.argv[4])startupSeed=Number(process.argv[4]);assert(Number.isInteger(startupSeed)&&startupSeed>=0&&startupSeed<65536);
initial.actualInitialTimeGetTimeInput=(Math.floor(originalClock/65536)*65536+startupSeed)>>>0;
const asset={replayPath:resolve(inputHome,key+'.rpy'),replaySha256:inputMeta.sha256};const archivePath=JSON.parse(readFileSync(resolve(R,'runtimes/th14/target.json'))).dataArchives['th14.dat'].path;assert.equal(sha(readFileSync(archivePath)),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
assert(music.passed&&music.tracks===18);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,n))),h);
mkdirSync(out);mkdirSync(resolve(out,'save'));copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(out,'save/th14.cfg'));

const put=(n,v)=>writeFileSync(resolve(out,n),JSON.stringify(v,null,2)+'\n');
writeFileSync(resolve(out,'executed-driver.mjs'),readFileSync(import.meta.filename));
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:initial.actualInitialTimeGetTimeInput,archivePath,fontDirectory:resolve(R,'artifacts/th14/stable-stage-close-nov07/runtime-ready/fonts'),saveDirectory:resolve(out,'save'),onAsyncError:e=>errors.push(String(e?.stack??e))});
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(out,'save'),'/music':musicDirectory}});
const instance=new WebAssembly.Instance(module,{env:platform.env,observerhost:{now_ns:()=>process.hrtime.bigint()},wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool);return pool.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const words=(name,n)=>Array.from(new Uint32Array(memory.buffer,c[name](),n));
const state=()=>words('behavior_state',20),error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
let phase='menu',phaseStart=0,frames=0,previous=-1,heldTicks=0,releasedTicks=0,created=false,closed=false,exception=null,passed=false;
let initialPosition,fastPosition,slowPosition,bombStock,freezeFrame,freezeCallbacks,maxShots=0,focusObserved=false,bombObserved=false,bombFinished=false,pausedAt=0;
const actions=[],checkpoints=[],began=performance.now();
const input=(held,label)=>{c.set_menu_input(held);actions.push({frame:frames,held,label});};
const step=(name,s)=>{phase=name;phaseStart=frames;checkpoints.push({name,frame:frames,state:s});};
const visitedStages=new Set(),boundaryCalls=[];let endingSeen=false,resultSeen=false,outcome='unknown',lastProgress=0,lastStage=0;
const keyFile=readFileSync(asset.replayPath);assert.equal(sha(keyFile),asset.replaySha256);
put('plan.json',{pid:process.pid,mode,maximumSeconds:360,maximumCallbacks:290000,actualApplicationAndCppThreads:true,
 completionBoundaryInvokedDirectly:false,naturalFullCampaignAccepted:false,
 onlyRecordedHeldMasksAndMenuKeys:true,recordedPositionStockScoreOrRngRestored:false,
 endOfSegmentPolicy:'keep firing; never emit all-FF terminal mask',graphicsRecordingOnly:true,silent:true,
 sourceReplaySha256:asset.replaySha256,sourceWasmSha256:sha(bytes),startupClockSelectedForDeterministicInputCoverage:true,originalClock,selectedClock:initial.actualInitialTimeGetTimeInput,startupSeed,expectedSeed,logicalTickDelta:1/60,logicalTickAccelerated:true,loadingAndMenusUseRealTimeCadence:true,noRngStateWrites:true,completeGame:false});

function driveMenu(){
 const m=words('menu_state',10);
 if(heldTicks){if(!--heldTicks){input(0,'menu-release');releasedTicks=8;}return;}
 if(releasedTicks){--releasedTicks;return;}
 if(m[1]!==2)return;
 let target=null,negative=16,positive=32;
 if(m[0]===1)target=0;else if(m[0]===5)target=difficulty;
 else if(m[0]===6){target=character;negative=64;positive=128;}
 else if(m[0]===7){target=subtype;negative=64;positive=128;}
 if(target===null)return;
 assert(actions.length<80,'bounded ordinary menu input');input(m[2]===target?1:m[2]>target?negative:positive,'menu-'+m[0]);heldTicks=2;
}
try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 assert(!('finish_live_boundary'in c));const keyPointer=c.allocate(keyFile.length);assert(keyPointer);try{new Uint8Array(memory.buffer,keyPointer,keyFile.length).set(keyFile);assert.equal(c.load_keys(keyPointer,keyFile.length),1);}finally{c.release(keyPointer);}
 while(performance.now()-began<360000&&frames<300000&&c.observation_count()<290000){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const timing=words('ordinary_timing_state',8),fast=!!timing[7];const before=c.frame_tick_count();assert(c.frame(fast?1/60:delta),error());frames=c.frame_tick_count();assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   const s=state(),f=words('ordinary_flow_state',24),menu=words('menu_state',10),keys=words('keyscript_state',12);
   assert.equal(f[2],0,'must remain ordinary game, never replay');assert.equal(keys[6],0);
   if(keys[4]&&keys[1])visitedStages.add(keys[1]);
   if(phase==='menu'){
    if(s[15]){assert.deepEqual(s.slice(1,5),[1,character,subtype,difficulty]);input(0,'game-release');step('natural-gameplay',s);const first=Array.from(new Uint32Array(memory.buffer,c.observation_data(),114));put('ordinary-initial-player.json',{behavior:s,flow:f,keys,firstPlayer:first,observedSeed:first[24],expectedSeed,startupSeed,initialSeedMatched:first[24]===expectedSeed});if(mode==='prefix'){outcome='ordinary-prefix-observed';passed=true;phase=outcome;break;}assert.equal(first[24],expectedSeed,'declared initial clock prediction');}else driveMenu();
   }else if(f[0]===3){
    outcome='natural-game-over';phase=outcome;put('natural-game-over.json',{behavior:s,flow:f,keys,pause:words('pause_save_state',12)});assert.equal(c.flush_save(),1,error());break;
   }else if(f[0]===5){
    if(!endingSeen){endingSeen=true;put('natural-ending-entered.json',{flow:f,behavior:s,keys});}
    c.set_menu_input(512|(frames%2?1:0));
   }else if(endingSeen&&f[0]===0&&f[5]===14&&f[23]===2){
    input(0,'results-release');resultSeen=true;assert.equal(visitedStages.size,6);
    assert.deepEqual(f.slice(7,11),[1,1,1,difficulty===0?1:0x11]);assert.equal(f[11],1);assert.deepEqual(f.slice(12,18),Array.from({length:6},(_,i)=>+(i===selection)));
    const observed=Buffer.from(new Uint8Array(memory.buffer,c.score_semantics_data(),c.score_semantics_size()));writeFileSync(resolve(out,'score-observed.bin'),observed);
    const offset=selection*0x5298+0x10+difficulty*0x118,rank={scoreUnits:observed.readUInt32LE(offset),stage:observed[offset+4],continues:observed[offset+5]};
    assert.equal(rank.stage,8);assert.equal(rank.continues,0);
    assert.equal(c.flush_save(),1,error());put('natural-result-and-flush.json',{flow:f,menu,behavior:s,keys,rank});passed=true;outcome='natural-clear-results-saved';phase=outcome;break;
   }
   if(f[1]!==lastStage||performance.now()-lastProgress>=10000){lastStage=f[1];lastProgress=performance.now();const progress={pid:process.pid,frames,callbacks:c.observation_count(),stage:f[1],phase:f[0],lives:s[19],normalSpeedUnits:s[16],keyState:keys,elapsedSeconds:(performance.now()-began)/1000};put('progress.json',progress);console.log(JSON.stringify(progress));}
  }
  if(!fast||frames===before)await new Promise(r=>setTimeout(r,1));else if(frames%16===0)await new Promise(r=>setTimeout(r,0));
 }
 if(outcome==='unknown')outcome=c.observation_count()>=290000?'callback-limit':frames>=300000?'frame-limit':'wall-limit';

}catch(e){exception=String(e?.stack??e);}
finally{
 if(created&&process.env.TH14_FLOW_STAGE_HEADERS==='1')try{
  assert.equal(typeof c.recorded_stage_headers,'function');
  const p=c.recorded_stage_headers(),n=c.recorded_stage_header_bytes();assert.equal(n,8*0xdc);
  writeFileSync(resolve(out,'recorded-stage-headers.bin'),Buffer.from(new Uint8Array(memory.buffer,p,n)));
 }catch(e){exception??=String(e?.stack??e);}
 try{if(created){put('before-close.json',{phase,state:state(),timing:words('ordinary_timing_state',8),stageSeeds:words('recorded_stage_seeds',32)});const n=c.observation_words();const tape=Buffer.from(new Uint32Array(memory.buffer,c.observation_data(),n).slice().buffer);put('observations-summary.json',{callbacks:c.observation_count(),words:n,bytes:tape.length,sha256:sha(tape),first:Array.from(new Uint32Array(tape.buffer,tape.byteOffset,Math.min(n,114))),last:Array.from(new Uint32Array(tape.buffer,tape.byteOffset+Math.max(0,n-114)*4,Math.min(n,114))),fullTapePersisted:false});c.close();closed=true;
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={terminal:true,pid:process.pid,passed:passed&&!exception&&retired&&!errors.length,character,subtype,difficulty,frames,phase,exception,errors,closed,retired,
 checkpoints,actions,maxActiveProjectiles:maxShots,focusObserved,bombObserved,bombFinished,initialPosition,fastPosition,slowPosition,workers,physicalWorkers:physical,
 sourceWasmSha256:sha(bytes),driverSha256:sha(readFileSync(resolve(out,'executed-driver.mjs'))),elapsedSeconds:(performance.now()-began)/1000,
 startupClockSelectedForDeterministicInputCoverage:true,originalClock,selectedClock:initial.actualInitialTimeGetTimeInput,startupSeed,expectedSeed,logicalTickDelta:1/60,logicalTickAccelerated:true,loadingAndMenusUseRealTimeCadence:true,noRngStateWrites:true,actualOrdinaryHeldInput:true,completionBoundaryInvokedDirectly:false,naturalFullCampaignAccepted:passed&&mode==='full',outcome,endingSeen,resultSeen,visitedStages:[...visitedStages],inputProviderIsHeldKeysOnly:true,recordedGameStateRestored:false,mode,referenceRowsFedBack:false,graphicsRecordingOnly:true,hardwareVisualAccepted:false,nativeAllModesCompared:false,completeGame:false};
put('report.json',report);
put('saved-files.json',readdirSync(resolve(out,'save'),{recursive:true,withFileTypes:true}).filter(e=>e.isFile()).map(e=>{const name=resolve(e.parentPath,e.name),b=readFileSync(name);return {name,bytes:b.length,sha256:sha(b)};}));
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({character,subtype,difficulty,passed:report.passed,phase,frames,exception,seconds:report.elapsedSeconds,bombFinished}));if(exception||!retired||!['ordinary-prefix-observed','natural-game-over','natural-clear-results-saved'].includes(outcome))process.exitCode=1;
