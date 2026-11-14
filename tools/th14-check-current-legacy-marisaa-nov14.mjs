import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/current-concurrent-mixer-nov14/replay-settings-gate');
const mode=process.argv[2]??'baseline',enabled=Number(process.argv[3]??0);assert(['baseline','candidate'].includes(mode)&&[0,1].includes(enabled));
const runName='legacy-marisaa-easy-current-v1';assert(/^[a-z0-9-]+$/.test(runName));
const O=resolve(H,runName);mkdirSync(O);mkdirSync(resolve(O,'save'));
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(H,'build.json')),bytes=readFileSync(resolve(H,mode+'.wasm'));
if(mode==='baseline')assert.equal(sha(bytes),build.probeWasm);
else assert.equal(sha(bytes),load(resolve(H,'candidate-build.json')).sha256);
const replayCase='legacy-marisaa-easy';
const replayCases={
 'legacy-marisaa-easy':['../royalflare-coverage-matrix-oct16/inputs/marisaa-easy.rpy','aec3b3045be9a0ddd4e7e4005182a9561e97f9d3f66f7f93a81397a1b614ec92'],
 practice:['beam-replay-rules/annotation-historical/optional-browser-saved-bounded.rpy','ff76b7ba4703d47cddee9ad962286348fa421db78893ceecb12fada73ed8d819'],
 ordinary:['browser-normal-persistence/ordinary-recording.rpy','e08a4420a91e6638abebfc371544724e383baa5490b8bf6142a3eac5ae245783'],
 events:['replay-settings-gate/controlled-tool-events.rpy','f45b27fad3e062c0fc287869693bdaa04d07b75a0ba1b3c2077eedc9a1254da3'],
};
assert(Object.hasOwn(replayCases,replayCase));
const [replayPath,replayHash]=replayCases[replayCase];
const input=readFileSync(resolve(H,'..',replayPath));assert.equal(sha(input),replayHash);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(O,'save/th14.cfg'));
const archivePath=JSON.parse(readFileSync(resolve(R,'runtimes/th14/target.json'))).dataArchives['th14.dat'].path;
assert.equal(sha(readFileSync(archivePath)),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
const put=(n,v)=>writeFileSync(resolve(O,n),JSON.stringify(v,null,2)+'\n');
writeFileSync(resolve(O,'executed-driver.mjs'),readFileSync(import.meta.filename));
put('plan.json',{mode,enabled,replayCase,inputSha256:sha(input),oneAttempt:true,configurationBeforeViewerOpenOnly:true,noReplayBytesOrGameEconomyOrRngWrites:true,silentMemoryAudioBackend:true,graphicsRecordingOnly:true,completeGame:false});
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationRecordingPlatform(module,memory,{clockInput:initial.actualInitialTimeGetTimeInput,archivePath,fontDirectory:resolve(R,'artifacts/th14/stable-stage-close-nov07/runtime-ready/fonts'),saveDirectory:resolve(O,'save'),onAsyncError:e=>errors.push(String(e?.stack??e))});
// CPU recording backend: retain the actual enable/disable stream for the
// renderer's capability queries. GL_DITHER is enabled by default in GLES.
// No raster or actual GPU claim is made.
const enabledCaps=new Set([0x0bd0]);let capabilityQueries=0;
for(const [name,down] of [['glEnable',true],['glDisable',false]]){
 const prior=platform.env[name];assert.equal(typeof prior,'function');
 platform.env[name]=cap=>{prior(cap);if(down)enabledCaps.add(cap);else enabledCaps.delete(cap);};
}
platform.env.glIsEnabled=cap=>{assert([0x0c11,0x0bd0].includes(cap),'only declared scissor/dither queries');capabilityQueries++;return +enabledCaps.has(cap);};
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(O,'save'),'/music':musicDirectory}});
const instance=new WebAssembly.Instance(module,{env:platform.env,observerhost:{now_ns:()=>process.hrtime.bigint()},wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>{const p=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(p);return p.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const words=(n,k)=>Array.from(new Uint32Array(memory.buffer,c[n](),k));
const strings=p=>{const b=new Uint8Array(memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
const nativeBytes=(b,fn,...args)=>{const p=c.viewer_alloc(b.length);assert(p);try{new Uint8Array(memory.buffer,p,b.length).set(b);return fn(p,b.length,...args);}finally{c.viewer_free(p);}};
let created=false,closed=false,exception=null,finished=false,description=null,opened=null,outcome=null,updates=0;const toolSamples=[];let lastSampleFrame=-1;
try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 const describe=nativeBytes(input,c.viewer_describe);assert(describe,'actual native metadata parser');description=JSON.parse(strings(describe));put('description.json',description);
 const limit=performance.now()+60000;let prior=-1;
 while(!c.viewer_ready()){
  assert(performance.now()<limit,'viewer readiness');const now=performance.now();assert(c.frame(prior<0?0:(now-prior)/1000),error());prior=now;
  await new Promise(r=>setTimeout(r,1));
 }
 assert.equal(c.viewer_practice_configure(enabled),1,'configuration input before open');
 assert.equal(nativeBytes(input,c.viewer_open,description.stages[0].id),1,error());
 opened=words('viewer_practice_observe',16);put('opened.json',{practice:opened,viewer:words('viewer_status',6)});
 const total=description.stages.reduce((n,s)=>n+s.frames,0),deadline=performance.now()+120000;
 while(!words('viewer_status',6)[3]){
  assert(performance.now()<deadline&&updates<total+10000,'bounded original replay');
  for(let i=0;i<16&&!words('viewer_status',6)[3];i++){
   assert(c.tick(),error());updates++;
   if(replayCase==='events'){
    const viewer=words('viewer_status',6),frame=viewer[1];
    if(frame!==lastSampleFrame&&[1,2,20,21,22,30,31,32,40].includes(frame)){
     lastSampleFrame=frame;toolSamples.push({updates,practice:words('viewer_practice_observe',16),viewer});
    }
   }
  }
  assert.equal(errors.length,0,errors.join('\n'));await new Promise(r=>setTimeout(r,0));
 }
 outcome={practice:words('viewer_practice_observe',16),state:words('behavior_state',20),viewer:words('viewer_status',6),outcome:words('outcome_state',12),callbacks:c.observation_count()};
 put('outcome.json',outcome);finished=true;
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){c.viewer_close();c.close();closed=true;const deadline=performance.now()+65000;while(platform.timers.size&&performance.now()<deadline)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={mode,enabled,replayCase,toolSamples,finished,exception,errors,retired,opened,outcome,updates,capabilityQueries,wasmSha256:sha(bytes),inputSha256:sha(input),silentMemoryAudioBackend:true,graphicsRecordingOnly:true,browserUiAccepted:false,completeGame:false};
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({mode,enabled,finished,retired,exception,practice:opened,score:outcome?.outcome?.[0]*10,frames:outcome?.viewer?.[1]}));
if(exception||errors.length||!retired||!finished)process.exitCode=1;
