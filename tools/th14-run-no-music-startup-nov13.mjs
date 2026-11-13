import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/no-music-startup-nov13');
const [variant,testcase]=process.argv.slice(2);assert(['before','after'].includes(variant));assert(['off-empty','on-real','on-empty','on-corrupt'].includes(testcase));const mode=testcase;
const character=0,subtype=1,difficulty=1,attempt='v2';
const out=resolve(H,variant+'-'+testcase),component=resolve(H,'component-'+variant);
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [n,h]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
const assets=resolve(R,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),asset=load(resolve(assets,'manifest.json'));assert(asset.passed);
assert.equal(sha(readFileSync(resolve(assets,'th14.dat'))),asset.referenceArchiveSha256);
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json'));
const realMusicDirectory=resolve(R,music.musicDirectory),musicDirectory=testcase==='on-real'?realMusicDirectory:resolve(out,'music');
mkdirSync(out);mkdirSync(resolve(out,'save'));copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(out,'save/th14.cfg'));
if(testcase!=='on-real'){mkdirSync(musicDirectory);if(testcase==='on-corrupt')writeFileSync(resolve(musicDirectory,'th14_01.ogg'),'invalid-vorbis');}
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
let phase='title',frames=0,previous=-1,heldTicks=0,releasedTicks=0,created=false,closed=false,exception=null,passed=false;
let stageTrack=null,continuedAt=0;const desiredFailure=['on-empty','on-corrupt'].includes(testcase);
const actions=[],checkpoints=[],began=performance.now();
const input=(key,label)=>{c.set_menu_input(key);actions.push({frame:frames,key,label});heldTicks=2;};
put('plan.json',{pid:process.pid,variant,testcase,musicEnabled:testcase!=='off-empty',musicAssets:testcase==='on-real'?'published Vorbis':testcase==='on-corrupt'?'declared invalid file':'empty',silent:true,desiredFailure,actualApplicationAndCppWorkers:true,completeGame:false});
function driveMenu(){
 const m=words('menu_state',10);if(m[1]!==2)return;let target=null,minus=16,plus=32;
 if(m[0]===1)target=0;else if(m[0]===5)target=1;else if(m[0]===6){target=0;minus=64;plus=128;}else if(m[0]===7){target=1;minus=64;plus=128;}
 if(target!==null){assert(actions.length<80);input(m[2]===target?1:m[2]>target?minus:plus,'menu-'+m[0]);}
}

try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 c.set_music_enabled(testcase!=='off-empty');
 while(performance.now()-began<75000&&frames<4500){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count();assert(c.frame(delta),error());frames=c.frame_tick_count();assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   const s=state(),menu=words('menu_state',10),audio=words('music_state',2),p=words('pause_save_state',12);
   if(heldTicks){if(!--heldTicks){c.set_menu_input(0);releasedTicks=8;}}else if(releasedTicks)--releasedTicks;
   else if(phase==='title'&&menu[0]===1&&menu[1]===2){
    checkpoints.push({name:'title-ready',frames,audio});if(testcase==='on-real'){passed=true;phase='title-ready';break;}phase='menus';driveMenu();
   }else if(phase==='menus'){
    if(s[15]){assert.deepEqual(s.slice(1,5),[1,0,1,1]);assert.equal(audio[0],0);stageTrack=audio[1];assert.notEqual(stageTrack,0xffffffff);phase='ordinary-gameplay';checkpoints.push({name:phase,frames,state:s,audio});}else driveMenu();
   }else if(phase==='ordinary-gameplay'&&s[0]===3){phase='game-over';checkpoints.push({name:phase,frames,state:s,audio,pause:p});}
   else if(phase==='game-over'&&p[0]===14){assert.equal(p[2],0);input(1,'continue');phase='continuing';}
   else if(phase==='continuing'&&s[0]===1&&s[19]===2){assert.equal(s[9],3);assert.equal(audio[1],stageTrack);continuedAt=s[15];phase='continued';checkpoints.push({name:phase,frames,state:s,audio});}
   else if(phase==='continued'&&s[15]>=continuedAt+30){passed=true;phase='continued-without-music-files';break;}

  }
  await new Promise(r=>setTimeout(r,1));
 }
 assert(passed,'Music-mode case did not reach its checkpoints: '+phase);
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){put('before-close.json',{phase,state:state()});const n=c.observation_words();writeFileSync(resolve(out,'observations.u32'),Buffer.from(new Uint32Array(memory.buffer,c.observation_data(),n).slice().buffer));c.close();closed=true;
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const failureVerified=desiredFailure&&!!exception&&/Unable to (?:decode|preload)/.test(exception);
const report={terminal:true,pid:process.pid,variant,testcase,passed:(passed||failureVerified)&&retired&&!errors.length,
 frames,phase,exception,expectedFailureVerified:failureVerified,errors,closed,retired,actions,checkpoints,workers,physicalWorkers:physical,
 sourceWasmSha256:sha(bytes),driverSha256:sha(readFileSync(resolve(out,'executed-driver.mjs'))),elapsedSeconds:(performance.now()-began)/1000,
 actualApplicationAndCppWorkers:true,graphicsRecordingOnly:true,silent:true,completeGame:false};
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({testcase,variant,passed:report.passed,phase,exception,retired,seconds:report.elapsedSeconds}));if(!report.passed)process.exitCode=1;
