import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {createReplayViewerHostTh14} from '../runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/native-viewer-application-nov13');
const mode='transport';
const out=resolve(H,'transport-v2'),save=resolve(out,'save'),component=resolve(H,'component-v3');
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [n,h]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
const assets=resolve(R,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),asset=load(resolve(assets,'manifest.json'));
assert(asset.passed);assert.equal(sha(readFileSync(resolve(assets,'th14.dat'))),asset.referenceArchiveSha256);
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
assert(music.passed&&music.tracks===18);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,n))),h);
mkdirSync(out);mkdirSync(save);copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(save,'th14.cfg'));
const put=(n,v)=>writeFileSync(resolve(out,n),JSON.stringify(v,null,2)+'\n');
writeFileSync(resolve(out,'executed-driver.mjs'),readFileSync(import.meta.filename));
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:initial.actualInitialTimeGetTimeInput,archivePath:resolve(assets,'th14.dat'),fontDirectory:resolve(R,'artifacts/th14/stable-stage-close-nov07/runtime-ready/fonts'),saveDirectory:save,onAsyncError:e=>errors.push(String(e?.stack??e))});
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':save,'/music':musicDirectory}});
const instance=new WebAssembly.Instance(module,{env:platform.env,observerhost:{now_ns:()=>process.hrtime.bigint()},wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool);return pool.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const words=(name,n)=>Array.from(new Uint32Array(memory.buffer,c[name](),n));
const error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));

let created=false,closed=false,exception=null,passed=false,paused=true,currentRate=1;
const events=[],checkpoints=[],began=performance.now(),ownedTimers=new Set();
const strings=p=>{const b=new Uint8Array(memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const file=readFileSync(resolve(R,'artifacts/th14/ordinary-replay-menu-nov13/write-c0-s1-d1-v2/save/replay/th14_01.rpy'));
const payloads=new Map([['replay/th14_01.rpy',file],['replay/th14_02.rpy',file]]);
const nativeBytes=(data,fn,...args)=>{const p=c.viewer_alloc(data.length);assert(p);try{new Uint8Array(memory.buffer,p,data.length).set(data);return fn(p,data.length,...args);}finally{c.viewer_free(p);}};
const controller=createReplayViewerHostTh14({
 read:path=>{assert(payloads.has(path));return {path,bytes:payloads.get(path)};},
 describe:bytes=>{const p=nativeBytes(bytes,c.viewer_describe);assert(p,'native descriptor');return JSON.parse(strings(p));},
 open:async(bytes,stage)=>{
  const until=performance.now()+60000;let prior=-1;
  while(!c.viewer_ready()){
   assert(performance.now()<until,'actual native open readiness timeout');const now=performance.now();assert(c.frame(prior<0?0:(now-prior)/1000),error());prior=now;
   await new Promise(resolve=>setTimeout(resolve,1));
  }
  await new Promise(resolve=>setTimeout(resolve,0));assert.equal(nativeBytes(bytes,c.viewer_open,stage),1,error());
 },
 status:()=>{const s=words('viewer_status',6);return {stage:s[0],frame:s[1],frames:s[2],ended:!!s[3],phase:s[4],active:!!s[5]};},
 step:(target,budget)=>c.viewer_seek(target,budget),
 rate:value=>{assert.equal(c.viewer_rate(value),1);currentRate=value;},pause:on=>{paused=on;},close:()=>c.viewer_close(),
 emit:state=>events.push({...state}),visible:()=>true,
 schedule:(fn,ms)=>{const t=setTimeout(()=>{ownedTimers.delete(t);void fn();},ms);ownedTimers.add(t);return t;},cancel:t=>{clearTimeout(t);ownedTimers.delete(t);},
 onError:e=>errors.push(String(e?.stack??e)),
});
const checkpoint=name=>{const record={name,state:controller.state,behavior:words('behavior_state',20),native:words('viewer_status',6),paused,currentRate};checkpoints.push(record);put('checkpoint-'+name+'.json',record);return record;};
const waitSeek=async()=>{const deadline=performance.now()+60000;while(controller.state?.seeking&&performance.now()<deadline){assert.equal(errors.length,0,errors.join('\n'));await new Promise(r=>setTimeout(r,5));}assert(!controller.state?.seeking,'bounded seek');assert.equal(errors.length,0,errors.join('\n'));};
put('plan.json',{pid:process.pid,oneAttempt:true,actualApplicationAndThreads:true,actualNativeOpenAndSeekMethods:true,nativeMetadataDecoder:true,maximumSeconds:180,silent:true,graphicsRecordingOnly:true,completeGame:false});
try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 assert.equal((await controller.command({action:'inspect',path:'replay/th14_01.rpy'})).description.character,0);
 await controller.command({action:'open',path:'replay/th14_01.rpy',stage:1});checkpoint('opened-cold');
 await controller.command({action:'pause'});assert(paused);
 await controller.command({action:'seek',value:150});await waitSeek();const first=checkpoint('seek150');assert.equal(first.state.frame,150);assert(paused);
 await controller.command({action:'seek',value:30});await waitSeek();assert.equal(controller.state.frame,30);checkpoint('seek30');
 await controller.command({action:'seek',value:150});await waitSeek();const repeated=checkpoint('seek150-repeat');assert.deepEqual(repeated.behavior.slice(1,15),first.behavior.slice(1,15));
 const rates={};for(const value of [.5,1,2,4,8,0]){
  await controller.command({action:'rate',value});let total=0;for(let n=0;n<120;n++)total+=c.viewer_clock(1/120);rates[String(value)]=total;
 }
 assert.deepEqual(rates,{'0.5':30,'1':60,'2':120,'4':240,'8':480,'0':1920});put('clock-rates.json',rates);
 await assert.rejects(controller.command({action:'rate',value:3}));await assert.rejects(controller.command({action:'seek',value:346}));
 await controller.command({action:'relocate',path:'replay/th14_01.rpy',target:'replay/th14_02.rpy'});assert.equal(controller.state.path,'replay/th14_02.rpy');assert.equal(controller.state.frame,150);
 await controller.command({action:'rate',value:1});await controller.command({action:'play'});assert(!paused);checkpoint('playing');
 await controller.command({action:'pause'});assert(paused);checkpoint('paused');
 await controller.command({action:'seek',value:345});await waitSeek();assert(controller.state.ended&&controller.state.paused);checkpoint('ended');
 await controller.command({action:'play'});assert(!controller.state.ended&&!paused);checkpoint('restarted-after-end');
 await controller.command({action:'pause'});await controller.command({action:'seek',value:150});await controller.close();
 await new Promise(r=>setTimeout(r,20));assert.equal(controller.state,null);assert.equal(ownedTimers.size,0);assert.equal(errors.length,0,errors.join('\n'));passed=true;
}catch(e){exception=String(e?.stack??e);}
finally{
 try{await controller.close();if(created){put('before-close.json',{status:words('viewer_status',6),behavior:words('behavior_state',20)});c.close();closed=true;const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!ownedTimers.size&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={terminal:true,pid:process.pid,passed:passed&&!exception&&retired&&!errors.length,exception,errors,retired,closed,checkpoints,events,workers,physicalWorkers:physical,sourceWasmSha256:sha(bytes),driverSha256:sha(readFileSync(resolve(out,'executed-driver.mjs'))),elapsedSeconds:(performance.now()-began)/1000,graphicsRecordingOnly:true,browserUiAccepted:false,completeGame:false};
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({passed:report.passed,exception,retired,seconds:report.elapsedSeconds}));if(!report.passed)process.exitCode=1;
