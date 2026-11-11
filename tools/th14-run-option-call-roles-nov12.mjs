// Real threaded Application + native ANGLE. References are compared only after shutdown.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,statfsSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationGlesPlatform} from './th14-full-application-gles-transition-type0-nov09.mjs';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/option-call-roles-nov12/current');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(p),load=p=>JSON.parse(read(p));
const component=resolve(root,'artifacts/th14/option-call-roles-nov12/component');
const buildRaw=read(resolve(component,'build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(component,'candidate.wasm'));
assert(build.actualColdApplicationInitializeTickAndDraw&&build.noDeclaredPerFileReadinessSchedule);
assert.equal(sha(wasm),build.outputs.candidate.wasmSha256);
assert.equal(sha(read(resolve(component,'fixture.cpp'))),build.fixtureSha256);
for(const [p,h]of Object.entries(build.sourceBindingsByMode.candidate))assert.equal(sha(read(resolve(root,p))),h,p);
for(const [p,h]of Object.entries(build.objectBindings))assert.equal(sha(read(resolve(root,p))),h,p);
const referenceDirectory=resolve(root,'artifacts/th14/option-startup-update-nov09/native');
// Only this external startup profile/configuration is extracted before the run.
const referenceRaw=read(resolve(referenceDirectory,'report.json'));
const profile=(()=>{const r=JSON.parse(referenceRaw),p=load(resolve(referenceDirectory,'untouched-first-player.json'));
 const receipt=load(resolve(referenceDirectory,'terminal-receipt.json'));
 assert(receipt.reaped&&receipt.exitCode===0&&r.childExited&&r.frameReadbackCompleted&&!r.error);
 assert(!r.debuggerAttached&&r.originalAttractFlagPreserved&&r.gameStateWrites===0);
 return{ticks:p.actualInitialTimeGetTimeInput,cookie:p.actualOriginalSecurityCookie,configHex:r.configHex};})();
const archive='H:/Games/th/14/th14.dat',archiveSha256=sha(read(archive));
assert.equal(archiveSha256,'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const runtime=resolve(root,'artifacts/th14/stable-stage-close-nov07/runtime-ready');
assert(statfsSync(root,{bigint:true}).bavail*statfsSync(root,{bigint:true}).bsize>=100n*1024n**3n);
if(process.argv.includes('--preflight')){const module=new WebAssembly.Module(wasm);const imports=WebAssembly.Module.imports(module);assert(!imports.some(x=>x.name.includes('__real__')||x.name.includes('__wrap__')));console.log(JSON.stringify({preflight:true,wasmSha256:sha(wasm),exports:WebAssembly.Module.exports(module).filter(x=>x.name.startsWith('option_role')),noInstanceCreated:true}));process.exit(0);}
mkdirSync(out);mkdirSync(resolve(out,'save'));mkdirSync(resolve(out,'save/replay'));
const put=(name,value)=>writeFileSync(resolve(out,name),JSON.stringify(value,null,2)+'\n');
writeFileSync(resolve(out,'save/th14.cfg'),Buffer.from(profile.configHex,'hex'));
const bindings={};for(const p of [import.meta.filename,'tools/th14-full-application-gles-transition-type0-nov09.mjs','tools/th14-node-angle-context-nov08.mjs','tools/th14-node-wasm-gles-nov08.mjs','tools/th14-full-application-recording-platform-texture-units-v2-nov07.mjs','tools/th14-wasi-stage-pool-observer-clock-nov07.mjs']){
 const path=resolve(root,p),bytes=read(path);bindings[relative(root,path).replaceAll('\\','/')]=sha(bytes);
 writeFileSync(resolve(out,path.split(/[\\/]/).at(-1)),bytes);
}
put('plan.json',{pid:process.pid,wasmSha256:sha(wasm),buildSha256:sha(buildRaw),bindings,referenceMetadataSha256:sha(referenceRaw),profile,
 archiveSha256,maximumSeconds:90,maximumFrames:4500,trigger:{publishedPlayerCallbacks:3},
 realApplication:true,realWasiThreads:true,actualGpu:true,originalArchiveUnmodified:true,heldInput:0,warmAttractClear:false,
 hostPollRequestedMs:1,actualFrameCadence:true,noPerFileReadinessSchedule:true,noRngOrCounterPadding:true,
 originalGameplayRowsUsedAsInputs:false,comparisonOnlyAfterTerminal:true,audibleOutput:false,completeGame:false});
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const platform=fullApplicationGlesPlatform(module,memory,{clockInput:profile.ticks,archivePath:archive,fontDirectory:resolve(runtime,'fonts'),
 saveDirectory:resolve(out,'save'),angleDirectory:'C:/Users/APKGG/AppData/Local/Programs/Trae',onAsyncError:e=>errors.push(String(e?.stack??e))});
platform.env.th14_async_schedule_impl=(callback,data,delay)=>{
 assert(callback>0&&delay>=0&&delay<=60000);
 const token=setTimeout(()=>{platform.timers.delete(token);try{c.async_deliver_owned(callback,data);}catch(e){errors.push(String(e?.stack??e));}},delay);platform.timers.add(token);
};
let phase='platform-created';process.on('exit',code=>put('exit-event.json',{code,phase,gpuContextClosed:platform.context.closed}));
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(out,'save'),'/music':resolve(runtime,'music')},returnOnExit:true});
const instance=new WebAssembly.Instance(module,{observerhost:{now_ns:()=>process.hrtime.bigint()},env:platform.env,
 wasi_snapshot_preview1:{...wasi.wasiImport,proc_exit:code=>{throw Error('Guest proc_exit '+code+' at '+phase);}},
 wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool,'Prepared worker');return pool.spawn(arg);}}});
const c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const words=(name,n)=>Array.from(new Uint32Array(memory.buffer,c[name](),n));
const error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
let frames=0,callbacks=0,created=false,closed=false,exception=null,capture=null,stoppedBy='unknown';
const states=[];let lastState=null,lastProgress=0,previous=-1;const began=performance.now();
try{
 phase='application-initialize';c.shot_snapshot_enable(0);created=true;assert.equal(c.begin(profile.ticks,profile.cookie,0),1,error());
 assert.equal(platform.getError(),0,'GPU initialization');phase='application-frames';
 while(frames<4500&&performance.now()-began<90000){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count()>>>0,ok=c.frame(delta);frames=c.frame_tick_count()>>>0;
  assert(ok,error());assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   assert.equal(platform.getError(),0,'GPU frame '+frames);callbacks=c.observation_count()>>>0;
   const state=words('state',16);
   if(!lastState||state.some((v,i)=>v!==lastState[i]))states.push({frame:frames,ms:performance.now()-began,words:state});lastState=state;
   if(callbacks){
    const n=c.observation_words()>>>0;assert.equal(n,callbacks*114);
    const row=Array.from(new Uint32Array(memory.buffer,c.observation_data()+(callbacks-1)*114*4,114));
    if(callbacks>=3){
     assert.equal(callbacks,3,'Do not silently overrun the callback bound');
     capture={frames,callbacks,latestBeforePlayerRow:row,state,readOnlyCallRoleObserver:true};
     put('capture.json',capture);stoppedBy='declared-target';break;
    }
   }
  }
  if(performance.now()-began-lastProgress>10000){lastProgress=performance.now()-began;put('progress.json',{pid:process.pid,frames,callbacks,state:lastState,elapsedSeconds:lastProgress/1000});console.log(JSON.stringify({frames,callbacks,state:lastState}));}
  await new Promise(r=>setTimeout(r,1));
 }
 if(stoppedBy==='unknown')stoppedBy=frames>=4500?'frame-limit':'wall-limit';
}catch(e){exception=String(e?.stack??e);stoppedBy='exception';}
finally{
 phase='application-close';
 try{if(created){
  writeFileSync(resolve(out,'observations.u32'),Buffer.from(new Uint32Array(memory.buffer,c.observation_data(),c.observation_words()).slice().buffer));

  c.close();closed=true;
  const roleCount=c.option_role_count()>>>0;
  assert(roleCount>0&&roleCount<=8192);
  writeFileSync(resolve(out,'option-call-roles.u32'),Buffer.from(new Uint32Array(memory.buffer,c.option_role_data(),roleCount*32).slice().buffer),{flag:'wx'});
  put('option-call-roles.json',{count:roleCount,stride:32,afterApplicationClose:true,noAgeRngOrReadinessInputs:true});
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);
 }}catch(e){exception??=String(e?.stack??e);}
 try{await Promise.all(pools.map(p=>p.shutdown()));clock.close();}catch(e){exception??=String(e?.stack??e);}
 try{put('platform-before-gpu-close.json',platform.summary());assert.equal(platform.getError(),0,'GPU teardown');}catch(e){exception??=String(e?.stack??e);}
 platform.closeGpu();
}
phase='terminal-audit';put('application-states.json',states);
const services=platform.summary();put('platform.json',services);
const resourceLeaks=Object.entries(services.actualNativeGles.liveObjects).filter(([,n])=>n!==0);
const platformRetired=!services.window&&!services.context&&!services.stream&&!services.openFiles&&!services.pendingTimers;
const comparison=null;
const report={terminal:true,pid:process.pid,stoppedBy,exception,errors,frames,callbacks,closed,platformRetired,resourceLeaks,
 wasmSha256:sha(wasm),referenceRowsOrPixelsReadDuringExecution:false,gpuContextClosed:platform.context.closed,workers:pools.flatMap(p=>p.summary()),physicalWorkers:pools.flatMap(p=>p.physicalSummary()),
 processClockResolution:clock.state,captureComplete:!!capture&&!exception&&!errors.length,comparison,
 boundedDiagnosticOnly:true,actualColdApplication:true,actualGpu:true,audibleOutput:false,completeGame:false,elapsedSeconds:(performance.now()-began)/1000};
put('report.json',report);phase='finished';console.log(JSON.stringify({stoppedBy,frames,callbacks,exception,resourceLeaks,platformRetired,differentPixels:comparison?.differentPixels}));
if(!report.captureComplete||resourceLeaks.length||!platformRetired)process.exitCode=1;
