import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ordinary-completion-flow-nov13');
const [mode]=process.argv.slice(2);assert(['write','read'].includes(mode));
const character=0,subtype=1,difficulty=1,attempt='v2';
const out=resolve(H,mode+'-v2'),component=resolve(H,'component-v2');
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [n,h]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
const assets=resolve(R,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),asset=load(resolve(assets,'manifest.json'));assert(asset.passed);
assert.equal(sha(readFileSync(resolve(assets,'th14.dat'))),asset.referenceArchiveSha256);
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
assert(music.passed&&music.tracks===18);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,n))),h);
mkdirSync(out);mkdirSync(resolve(out,'save'));copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(out,'save/th14.cfg'));
if(mode==='read')for(const name of ['scoreth14.dat','th14.cfg'])copyFileSync(resolve(H,'write-v2/save',name),resolve(out,'save',name));
const put=(n,v)=>writeFileSync(resolve(out,n),JSON.stringify(v,null,2)+'\n');
writeFileSync(resolve(out,'executed-driver.mjs'),readFileSync(import.meta.filename));
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:initial.actualInitialTimeGetTimeInput,archivePath:resolve(assets,'th14.dat'),fontDirectory:resolve(R,'artifacts/th14/stable-stage-close-nov07/runtime-ready/fonts'),saveDirectory:resolve(out,'save'),onAsyncError:e=>errors.push(String(e?.stack??e))});
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
const completedStages=new Set(),boundaryCalls=[];let endingSeen=false,resultSeen=false;
put('plan.json',{pid:process.pid,mode,maximumSeconds:360,actualApplicationAndCppThreads:true,
 completionBoundaryInvokedDirectly:mode==='write',naturalFullCampaignAccepted:false,
 onlyHeldMenuKeysAndCompletionMethod:true,scoreClearFlagsOrRngWritten:false,graphicsRecordingOnly:true,silent:true,completeGame:false});

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
 while(performance.now()-began<360000&&frames<21600){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count();assert(c.frame(delta),error());frames=c.frame_tick_count();assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   const s=state(),f=words('completion_flow_state',24),menu=words('menu_state',10);
   if(mode==='read'){
    if(menu[0]===1&&menu[1]===2){
     assert.deepEqual(f.slice(7,11),[1,1,1,0x11]);assert.equal(f[11],1);assert.deepEqual(f.slice(12,18),[0,1,0,0,0,0]);
     put('fresh-title-read.json',{flow:f,menu,behavior:s});passed=true;phase='fresh-title-restored';break;
    }
   }else if(phase==='menu'){
    if(s[15]){assert.deepEqual(s.slice(1,5),[1,character,subtype,difficulty]);input(0,'game-release');step('live-stages',s);}else driveMenu();
   }else if(f[0]===1&&s[8]===1&&s[5]>=10&&!completedStages.has(f[1])&&c.completion_boundary_ready()){
    assert(f[1]>=1&&f[1]<=6);assert.equal(f[2],0);const before=f;
    assert.equal(c.finish_live_boundary(),1,error());completedStages.add(f[1]);const after=words('completion_flow_state',24);
    boundaryCalls.push({stage:f[1],frame:frames,before,after});put('boundary-calls.json',boundaryCalls);
    console.log(JSON.stringify({mode,stageCompleted:f[1],frames}));
   }else if(f[0]===5){
    if(!endingSeen){endingSeen=true;put('ending-entered.json',{flow:f,behavior:s});}
    c.set_menu_input(512|(frames%2?1:0));
   }else if(endingSeen&&f[0]===0&&f[5]===14&&f[23]===2){
    input(0,'results-release');resultSeen=true;assert.equal(completedStages.size,6);
    assert.deepEqual(f.slice(7,11),[1,1,1,0x11]);assert.equal(f[11],1);assert.deepEqual(f.slice(12,18),[0,1,0,0,0,0]);
    assert.equal(c.flush_save(),1,error());put('result-and-flush.json',{flow:f,menu,behavior:s});passed=true;phase='results-saved';break;
   }
  }
  await new Promise(r=>setTimeout(r,1));
 }
 assert(passed,'Behavior case did not reach all declared checkpoints: '+phase);
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){put('before-close.json',{phase,state:state()});const n=c.observation_words();writeFileSync(resolve(out,'observations.u32'),Buffer.from(new Uint32Array(memory.buffer,c.observation_data(),n).slice().buffer));c.close();closed=true;
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={terminal:true,pid:process.pid,passed:passed&&!exception&&retired&&!errors.length,character,subtype,difficulty,frames,phase,exception,errors,closed,retired,
 checkpoints,actions,maxActiveProjectiles:maxShots,focusObserved,bombObserved,bombFinished,initialPosition,fastPosition,slowPosition,workers,physicalWorkers:physical,
 sourceWasmSha256:sha(bytes),driverSha256:sha(readFileSync(resolve(out,'executed-driver.mjs'))),elapsedSeconds:(performance.now()-began)/1000,
 actualOrdinaryHeldInput:true,completionBoundaryInvokedDirectly:mode==='write',naturalFullCampaignAccepted:false,endingSeen,resultSeen,boundaryCalls,mode,referenceRowsFedBack:false,graphicsRecordingOnly:true,hardwareVisualAccepted:false,nativeAllModesCompared:false,completeGame:false};
put('report.json',report);
put('saved-files.json',readdirSync(resolve(out,'save'),{recursive:true,withFileTypes:true}).filter(e=>e.isFile()).map(e=>{const name=resolve(e.parentPath,e.name),b=readFileSync(name);return {name,bytes:b.length,sha256:sha(b)};}));
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({character,subtype,difficulty,passed:report.passed,phase,frames,exception,seconds:report.elapsedSeconds,bombFinished}));if(!report.passed)process.exitCode=1;
