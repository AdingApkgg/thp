import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ordinary-difficulties-nov14');
const mode='read',key=process.argv[2]??'marisaa-easy',writerVersion=process.argv[3]??'v4';assert(/^(reimu|marisa|sakuya)[ab]-(easy|normal|hard|lunatic)$/.test(key));assert(['v3','v4'].includes(writerVersion));
const inputHome=resolve(R,process.env.TH14_FLOW_INPUT_DIR??'artifacts/th14/royalflare-coverage-matrix-oct16/inputs'),inputMeta=JSON.parse(readFileSync(resolve(inputHome,key+'-source.json'))),character=inputMeta.character,subtype=inputMeta.subtype,difficulty=inputMeta.difficulty,selection=character*2+subtype;
const runName=process.env.TH14_FLOW_OUTPUT??key+'-gameover-continue-fresh-v2';assert(/^[a-z0-9_-]+$/.test(runName));
const out=resolve(H,runName),component=resolve(R,process.env.TH14_FLOW_COMPONENT??'artifacts/th14/ordinary-difficulties-nov14/canonical-component');
const sourceSave=process.env.TH14_FLOW_SOURCE_SAVE;assert(sourceSave,'TH14_FLOW_SOURCE_SAVE must identify the saved ordinary run directory');
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [n,h]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
const archivePath=JSON.parse(readFileSync(resolve(R,'runtimes/th14/target.json'))).dataArchives['th14.dat'].path;
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
assert(music.passed&&music.tracks===18);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,n))),h);
mkdirSync(out);mkdirSync(resolve(out,'save'));copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(out,'save/th14.cfg'));
if(mode==='read')for(const name of ['scoreth14.dat','th14.cfg'])copyFileSync(resolve(R,sourceSave,name),resolve(out,'save',name));
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
const completedStages=new Set(),boundaryCalls=[];let endingSeen=false,resultSeen=false;
put('plan.json',{pid:process.pid,mode,maximumSeconds:90,actualApplicationAndCppThreads:true,
 completionBoundaryInvokedDirectly:false,naturalFullCampaignAccepted:false,
 readOnlyFreshTitleAvailability:true,completionMethodNotExported:true,scoreClearFlagsOrRngWritten:false,graphicsRecordingOnly:true,silent:true,completeGame:false});


try{
 const keyFile=readFileSync(resolve(inputHome,key+'.rpy')),pointer=c.allocate(keyFile.length);new Uint8Array(memory.buffer,pointer,keyFile.length).set(keyFile);assert.equal(c.load_keys(pointer,keyFile.length),1);c.release(pointer);
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 while(performance.now()-began<90000&&frames<5400){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count();assert(c.frame(delta),error());frames=c.frame_tick_count();assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   const s=state(),f=words('ordinary_flow_state',24),menu=words('menu_state',10);
   if(menu[0]===1&&menu[1]===2){
    assert.deepEqual(f.slice(7,11),[0,0,0,0]);assert.equal(f[11],0);assert.deepEqual(f.slice(12,18),Array.from({length:6},()=>0));
    assert.equal(c.observation_count(),0);assert(!('finish_live_boundary' in c));
    writeFileSync(resolve(out,'score-observed.bin'),Buffer.from(new Uint8Array(memory.buffer,c.score_semantics_data(),c.score_semantics_size())));const bytes=Buffer.from(new Uint8Array(memory.buffer,c.score_semantics_data(),c.score_semantics_size())),offset=selection*0x5298+0x10+difficulty*0x118;assert.equal(bytes.readUInt32LE(offset),8243413);assert.deepEqual([...bytes.subarray(offset+4,offset+6)],[3,0]);put('fresh-title-read.json',{flow:f,menu,behavior:s});passed=true;phase='fresh-title-restored';break;
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
 actualOrdinaryHeldInput:false,freshSavedTitleReadOnly:true,completionBoundaryInvokedDirectly:false,naturalFullCampaignAccepted:false,endingSeen,resultSeen,boundaryCalls,mode,referenceRowsFedBack:false,graphicsRecordingOnly:true,hardwareVisualAccepted:false,nativeAllModesCompared:false,completeGame:false};
put('report.json',report);
put('saved-files.json',readdirSync(resolve(out,'save'),{recursive:true,withFileTypes:true}).filter(e=>e.isFile()).map(e=>{const name=resolve(e.parentPath,e.name),b=readFileSync(name);return {name,bytes:b.length,sha256:sha(b)};}));
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({character,subtype,difficulty,passed:report.passed,phase,frames,exception,seconds:report.elapsedSeconds,bombFinished}));if(!report.passed)process.exitCode=1;
