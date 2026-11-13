import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ordinary-replay-menu-nov13');
const args=process.argv.slice(2);assert(args.length===3||args.length===4);
const [character,subtype,difficulty]=args.slice(0,3).map(Number);assert(character>=0&&character<3&&[0,1].includes(subtype)&&difficulty>=0&&difficulty<4);
const attempt=args[3]??'v2';assert(/^v[2-9][0-9]*$/.test(attempt));
const out=resolve(H,`death-continue-c${character}-s${subtype}-d${difficulty}-${attempt}`),component=resolve(H,'component');
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
put('plan.json',{pid:process.pid,character,subtype,difficulty,attempt,oneAttempt:true,heldKeysAndPauseEventOnly:true,maximumSeconds:240,naturalDamageAndOrdinaryContinue:true,maximumFrames:14400,
 completeBombLifetimeRequired:difficulty===1,actualApplicationAndThreads:true,graphicsRecordingOnly:true,publishedVorbis18:true,ordinaryNonReplay:true,warmAttract:false,
 wasmSha256:sha(bytes),driverSha256:sha(readFileSync(import.meta.filename)),noReferenceRowsSupplied:true,completeGame:false});
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
 while(performance.now()-began<240000&&frames<14400){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count();assert(c.frame(delta),error());frames=c.frame_tick_count();assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   const s=state();maxShots=Math.max(maxShots,s[11]);focusObserved||=s[12]===1;
   if(phase==='menu'){
    if(s[15]){assert.deepEqual(s.slice(1,5),[1,character,subtype,difficulty]);input(0,'game-release');step('wait-player',s);}else driveMenu();

   }else if(phase==='wait-player'&&s[0]===1&&s[8]===1&&s[15]>=90){
    input(0,'idle-natural-damage');step('idle',s);
   }else if(phase==='idle'){
    if(!checkpoints.length||checkpoints.at(-1).state?.[19]!==s[19])checkpoints.push({name:'life-stock-change',frame:frames,state:s});
    if(s[0]===3){step('game-over',s);}
   }else if(phase==='game-over'){
    const p=words('pause_save_state',12);
    if(p[0]===14&&p[1]>=10){assert.equal(p[2],0,'continue selected');input(1,'continue-confirm');step('continue-key',s);}
    else if(p[0]===18&&p[1]>=10){assert.fail('ranked name entry requires a declared next fixture step');}
   }else if(phase==='continue-key'&&frames-phaseStart>=2){input(0,'continue-release');step('wait-continued',s);}
   else if(phase==='wait-continued'&&s[0]===1&&s[8]!==1){
    if(!checkpoints.some(x=>x.name==='continue-respawn-tail')){assert.equal(s[9],3,'completed death update restores respawn bombs');assert.equal(s[19],2);checkpoints.push({name:'continue-respawn-tail',frame:frames,state:s});}
   }else if(phase==='wait-continued'&&s[0]===1&&s[8]===1){
    assert.equal(s[19],2,'continue restores lives');assert.equal(s[9],3,'normal respawn restores three bombs');assert.equal(s[18],400,'continue restores maximum power');
    c.press_pause();step('wait-continued-pause',s);
   }else if(phase==='wait-continued-pause'&&s[0]===2&&s[14]===3){
    const p=words('campaign_end_state',18);assert.equal(p[9],1,'continued run disables replay saving');put('continue-pause.json',{end:p,behavior:s});
    input(0x10000,'return-title-after-continue');step('title-key',s);
   }else if(phase==='title-key'&&frames-phaseStart>=2){input(0,'title-release');step('wait-title',s);}
   else if(phase==='wait-title'){
    const m=words('menu_state',10);if(m[0]===1&&m[1]===2){step('passed',s);passed=true;break;}
   }
   if(!['menu','idle'].includes(phase))assert(frames-phaseStart<1100,'bounded behavior phase '+phase);
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
 actualOrdinaryHeldInput:true,referenceRowsFedBack:false,graphicsRecordingOnly:true,hardwareVisualAccepted:false,nativeAllModesCompared:false,completeGame:false};
put('report.json',report);
put('saved-files.json',readdirSync(resolve(out,'save'),{recursive:true,withFileTypes:true}).filter(e=>e.isFile()).map(e=>{const name=resolve(e.parentPath,e.name),b=readFileSync(name);return {name,bytes:b.length,sha256:sha(b)};}));
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({character,subtype,difficulty,passed:report.passed,phase,frames,exception,seconds:report.elapsedSeconds,bombFinished}));if(!report.passed)process.exitCode=1;
