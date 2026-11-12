import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,statfsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationGlesPlatform} from './th14-full-application-sized-gles-nov12.mjs';
const mode=Number(process.argv[process.argv.indexOf('--mode')+1]);assert([3,4,5].includes(mode));
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/display-mode-entry-nov12/application');
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const driverSource=read(import.meta.filename),driverSha256=sha(driverSource);
const nativeHome=resolve(root,'artifacts/th14/native-natural-title-exit-nov12-v2');
const nativeReportRaw=read(resolve(nativeHome,'report.json')),nativeReport=JSON.parse(nativeReportRaw);
assert(nativeReport.reaped&&nativeReport.exitCode===0&&nativeReport.naturalOsExitObserved);
assert(!nativeReport.observerTerminationRequested&&nativeReport.quietRuntimeMeasured&&nativeReport.immutableAssetsUnchanged);
const receipt=load(resolve(root,'artifacts/th14/native-natural-title-exit-nov12-v2/terminal-receipt.json'));
assert(receipt.reaped&&receipt.exitCode===0);
const component=resolve(home,'component'),buildRaw=read(resolve(component,'build.json')),build=JSON.parse(buildRaw);
for(const [path,digest]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(read(resolve(root,path))),digest,path);
const wasm=read(resolve(component,'candidate.wasm'));assert.equal(sha(wasm),build.wasmSha256);
assert.equal(sha(read(resolve(component,'fixture.cpp'))),build.fixtureSha256);
assert(build.ordinaryKeyboardInputExport&&build.exitSaveUsesProductionMethodAfterFinishedOnly);
const storage=statfsSync(root,{bigint:true});assert(storage.bavail*storage.bsize>=100n*1024n**3n);
if(process.argv.includes('--preflight')){const m=new WebAssembly.Module(wasm);assert(WebAssembly.Module.exports(m).some(x=>x.name==='held_input'));assert(WebAssembly.Module.exports(m).some(x=>x.name==='exit_save'));console.log(JSON.stringify({preflight:true,wasmSha256:sha(wasm),gameInstantiated:false,originalTitleQuitUiAccepted:false}));process.exit(0);}
const out=resolve(home,`run-v2-mode${mode}`);mkdirSync(out);mkdirSync(resolve(out,'save'));mkdirSync(resolve(out,'save/replay'));
const config=Buffer.from(read(resolve(nativeHome,'initial-config.bin')));assert(config[0x22]===0&&config[0x23]===0);config[0x1f]=mode;writeFileSync(resolve(out,'save/th14.cfg'),config);
writeFileSync(resolve(out,'run-host.mjs'),driverSource);
const put=(name,value)=>writeFileSync(resolve(out,name),JSON.stringify(value,null,2)+'\n');
const profile=load(resolve(root,'artifacts/th14/player-entry-end-menu-nov06/campaign/untouched-first-player.json'));
const runtime=resolve(root,'artifacts/th14/stable-stage-close-nov07/runtime-ready');
const module=await WebAssembly.compile(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true}),errors=[];
const nativeModes=load(resolve(root,'artifacts/th14/display-mode-entry-nov12/native.json'));const nativeMode=nativeModes.rows.find(r=>r.mode===mode);assert(nativeMode);
const nativeContext=load(resolve(root,'artifacts/th14/display-mode-entry-nov12/context-native-v2/report.json')).rows.find(r=>r.mode===mode&&r.resource===1).stages[1];
const platform=fullApplicationGlesPlatform(module,memory,{renderWidth:nativeMode.width,renderHeight:nativeMode.height,clockInput:profile.actualInitialTimeGetTimeInput,
 archivePath:resolve(nativeHome,'work/th14.dat'),fontDirectory:resolve(runtime,'fonts'),saveDirectory:resolve(out,'save'),
 angleDirectory:'C:/Users/APKGG/AppData/Local/Programs/Trae',onAsyncError:e=>errors.push(String(e?.stack??e))});
const pools=[0,1].map(()=>new Th14WasiStagePool(module,memory,{onError:e=>errors.push(String(e))}));pools[1].nextTid=100000;
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/save':resolve(out,'save'),'/music':resolve(runtime,'music')}});
let c;
platform.env.th14_async_schedule_impl=(callback,data,delay)=>{assert(callback>0&&delay>=0&&delay<=60000);const token=setTimeout(()=>{platform.timers.delete(token);try{c.async_deliver_owned(callback,data);}catch(e){errors.push(String(e?.stack??e));}},delay);platform.timers.add(token);};
const instance=await WebAssembly.instantiate(module,{observerhost:{now_ns:()=>process.hrtime.bigint()},env:platform.env,
 wasi_snapshot_preview1:wasi.wasiImport,wasi:{'thread-spawn':arg=>{const pool=pools.find(p=>p.slot?.ready&&!p.slot.busy);assert(pool,'No ready worker');return pool.spawn(arg);}}});
c=instance.exports;platform.attach(c);wasi.initialize(instance);await Promise.all(pools.map(p=>p.prewarm()));
const clock=beginTh14ProcessClockResolution(s=>put('process-clock.json',s));
const state=()=>Array.from(new Uint32Array(memory.buffer,c.title_state(),10));
const error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
put('plan.json',{pid:process.pid,wasmSha256:sha(wasm),buildSha256:sha(buildRaw),nativeReportSha256:sha(nativeReportRaw),
 initialConfigSha256:sha(config),changedConfigByte:0x1f,selectedDisplayMode:mode,maximumSeconds:180,maximumFrames:2400,
 clockAndCookieFromRetainedNormalProfile:true,freshNativeClockNotMeasured:true,ordinaryHeldMasksOnly:[0,2],
 nativeStateOrTimingRowsSupplied:false,expectedGameplayCallbacks:0,originalUiEvidenceRequiredSeparately:true,completeGame:false});
let created=false,closed=false,saved=false,displayCaptured=false,exception=null,stage='wait-title',frames=0,inputAt=-1,previous=null,last=null;
const actions=[],states=[],began=performance.now();
function input(held,label){assert.equal(c.held_input(held),1);inputAt=frames;actions.push({label,held,frame:frames,state:state()});}
function captureDisplay(){
 const actual=Array.from(new Uint32Array(memory.buffer,c.display_state(),37));
 const {width,height}=nativeMode;
 assert.deepEqual(actual.slice(0,11),[mode,width,height,width,height,width*4,width,height,width*2,width,height]);
 assert.deepEqual(actual.slice(11,16),nativeContext.slice(0,5));
 for(let i=0;i<4;i++)assert.deepEqual(actual.slice(16+i*4,20+i*4),nativeContext.slice(5+i*8,9+i*8));
 assert.equal(actual[36],37);

 const targetCount=c.display_target_count();assert.equal(targetCount,10);
 const targetWords=Array.from(new Uint32Array(memory.buffer,c.display_target_words(),targetCount*16));
 const targetNative=load(resolve(root,'artifacts/th14/display-mode-entry-nov12/targets-native-v2/native.json')).rows.find(r=>r.name==='text.anm'&&r.renderWidth===width);
 const targetRows=targetNative.sprites.filter(s=>s.texture>=2);
 assert.equal(targetRows.length,targetCount);
 for(let i=0;i<targetCount;i++)assert.deepEqual(targetWords.slice(i*16,i*16+16),[targetRows[i].index,targetRows[i].texture,...targetRows[i].words.slice(3,17)]);
 put('targets.json',{targetCount,words:targetWords,comparedNativeWords:targetCount*14,rawSpriteIdentityPreserved:true});
 const pixels=platform.readBGRA();assert.equal(pixels.length,width*height*4);
 let varied=0;for(let i=4;i<pixels.length;i+=4)if(!pixels.subarray(i,i+4).equals(pixels.subarray(0,4)))++varied;
 assert(varied>100,'Title frame must contain visible geometry');
 writeFileSync(resolve(out,'title.bgra'),pixels);
 put('display.json',{mode,width,height,actualWords:actual,frame:frames,pixelsBytes:pixels.length,pixelsSha256:sha(pixels),pixelsDifferentFromTopLeft:varied,
  nativeContextWordsCompared:21,nativeWholeFramePixelComparison:false,completeGame:false});displayCaptured=true;
}
try{
 assert.equal(c.shot_snapshot_enable(0),1);created=true;
 assert.equal(c.begin(profile.actualInitialTimeGetTimeInput,profile.actualOriginalSecurityCookie,0),1,error());
 while(performance.now()-began<180000&&frames<2400){
  const now=performance.now(),delta=previous===null?0:(now-previous)/1000;previous=now;
  const ok=c.frame(delta);frames=c.frame_tick_count()>>>0;
  const s=state();if(!last||s.some((v,i)=>v!==last[i]))states.push({frame:frames,ms:performance.now()-began,words:s});last=s;
  assert.equal(c.observation_count(),0,'Attract playback entered before ordinary Quit');
  assert.equal(platform.getError(),0);assert.equal(errors.length,0,errors.join('\n'));
  if(s[0]===4){assert.equal(stage,'wait-finish');assert.equal(c.exit_save(),1,error());saved=true;stage='finished';break;}
  if(!ok)throw Error(error());
  if(stage==='wait-title'&&s[0]===0&&s[1]===1&&s[2]===1&&s[3]===2){assert.equal(s[4],0);captureDisplay();input(2,'escape-select-Quit');stage='release-first';}
  else if(stage==='release-first'&&frames>inputAt){input(0,'release-first-Escape');stage='wait-Quit-selection';}
  else if(stage==='wait-Quit-selection'&&frames>=inputAt+2&&s[0]===0&&s[2]===1&&s[3]===2&&s[4]===9){input(2,'escape-confirm-Quit');stage='release-second';}
  else if(stage==='release-second'&&frames>inputAt){input(0,'release-second-Escape');stage='wait-finish';}
  await new Promise(r=>setTimeout(r,1));
 }
 assert(saved&&displayCaptured&&stage==='finished','Ordinary Quit/display did not finish within declared bounds');
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){c.close();closed=true;const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));clock.close();
 try{platform.closeGpu();}catch(e){exception??=String(e?.stack??e);}
}
const summary=platform.summary();put('platform.json',summary);put('actions.json',actions);put('states.json',states);
const report={selectedDisplayMode:mode,displayCaptured,pid:process.pid,terminal:true,closed,stage,frames,exception,errors,exitSaveExecuted:saved,
 elapsedSeconds:(performance.now()-began)/1000,driverSha256,wasmSha256:sha(wasm),
 workers:pools.flatMap(p=>p.summary()),physicalWorkers:pools.flatMap(p=>p.physicalSummary()),processClockResolution:clock.state,
 ordinaryInputOnly:true,actualGles:true,quiet:!summary.audibleOutput,nativeFilesNotComparedDuringExecution:true,
 nativeUiOrSaveEqualityAccepted:false,completeGame:false};put('report.json',report);console.log(JSON.stringify(report));
if(exception||!saved)process.exitCode=1;
