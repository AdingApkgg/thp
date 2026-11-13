import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ordinary-config-reopen-nov13');
const mode=process.argv[2];assert(['write','reopen'].includes(mode));
const out=resolve(H,mode),save=resolve(H,'save'),component=resolve(H,'component');
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(component,'build.json')),bytes=readFileSync(resolve(component,'candidate.wasm'));
assert.equal(sha(bytes),build.outputs.candidate.wasmSha256);
for(const [n,h]of Object.entries({...build.sourceBindingsByMode.candidate,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(R,n))),h,n);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
const assets=resolve(R,'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),asset=load(resolve(assets,'manifest.json'));
assert(asset.passed);assert.equal(sha(readFileSync(resolve(assets,'th14.dat'))),asset.referenceArchiveSha256);
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
assert(music.passed&&music.tracks===18);for(const [n,h]of Object.entries(music.sha256))assert.equal(sha(readFileSync(resolve(musicDirectory,n))),h);
mkdirSync(out);if(mode==='write'){mkdirSync(save);copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(save,'th14.cfg'));}
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
const config=()=>Buffer.from(new Uint8Array(memory.buffer,c.config_data(),92));
const semantics=()=>{
 const p=c.score_semantics_data(),b=Buffer.from(new Uint8Array(memory.buffer,p,c.score_semantics_size()));
 writeFileSync(resolve(out,'score-raw-observed.bin'),b);
 assert.equal(b.length,7*0x5298+0x42c);
 // Serialization fills record checksums and character indices on a copy.
 // Retain raw bytes; compare every remaining record byte, including RNG filler.
 for(let i=0;i<7;i++){assert.equal(b.readUInt32LE(i*0x5298),0x15243);b.fill(0,i*0x5298+4,i*0x5298+8);b.fill(0,i*0x5298+12,i*0x5298+16);}
 assert.equal(b.readUInt32LE(7*0x5298),0x15453);b.fill(0,7*0x5298+4,7*0x5298+8);return b;
};
const error=()=>new TextDecoder().decode(new Uint8Array(memory.buffer,c.error_data(),c.error_size()));
let phase='main',frames=0,previous=-1,held=0,release=0,created=false,closed=false,passed=false,exception=null,baseline=null,expected=null;
const actions=[],checkpoints=[],began=performance.now();
const input=(key,label)=>{c.set_menu_input(key);actions.push({frame:frames,key,label});held=2;};
const step=(name)=>{phase=name;checkpoints.push({phase,frame:frames,menu:words('menu_state',10),config:[...config()]});};
put('plan.json',{pid:process.pid,mode,maximumSeconds:90,actualMenuInputOnly:true,configChangesNotInjected:true,hostFlushCallsSameApplicationSaveAsProductionExport:true,readOnlyConfigAndScoreObservations:true,graphicsRecordingOnly:true,actualSilentMixer:true,completeGame:false});
try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 while(performance.now()-began<90000){
  const now=performance.now(),delta=previous<0?0:(now-previous)/1000;previous=now;
  const before=c.frame_tick_count();assert(c.frame(delta),error());frames=c.frame_tick_count();assert.equal(errors.length,0,errors.join('\n'));
  if(frames>before){
   const m=words('menu_state',10);
   if(held){if(!--held){c.set_menu_input(0);release=8;}}else if(release){--release;}
   else if(phase==='main'&&m[0]===1&&m[1]===2){
    if(!baseline){baseline=config();if(mode==='reopen'){
      expected=load(resolve(H,'write/expected.json'));assert.deepEqual([...config()],expected.config);assert.equal(sha(semantics()),expected.scoreSemanticsSha256);
    }}
    if(m[2]===7){input(1,'open-options');step('options');}else input(m[2]>7?16:32,'select-options');
   }else if(phase==='options'&&m[0]===3&&m[1]===2){
    assert.equal(m[2],0);
    if(mode==='write'){input(baseline[0x22]>=5?64:128,'music-volume-step-five');step('music-edited');}
    else {assert.deepEqual([...config()],expected.config);input(2,'options-select-return');step('options-return');}
   }else if(phase==='music-edited'){
    assert.equal(config()[0x22],baseline[0x22]+(baseline[0x22]>=5?-5:5));input(32,'select-sound-volume');step('sound-row');
   }else if(phase==='sound-row'){
    assert.equal(m[2],1);input(baseline[0x23]>=5?64:128,'sound-volume-step-five');step('sound-edited');
   }else if(phase==='sound-edited'){
    assert.equal(config()[0x23],baseline[0x23]+(baseline[0x23]>=5?-5:5));input(2,'options-select-return');step('options-return');
   }else if(phase==='options-return'){
    assert.equal(m[2],4);input(2,'options-return-confirm');step('wait-main');
   }else if(phase==='wait-main'&&m[0]===1&&m[1]===2){
    const cfg=config(),score=semantics();assert.equal(c.flush_save(),1,error());
    assert.deepEqual(readFileSync(resolve(save,'th14.cfg')),cfg);assert(readFileSync(resolve(save,'scoreth14.dat')).length>24);
    if(mode==='write')put('expected.json',{config:[...cfg],scoreSemanticsSha256:sha(score),scoreSemanticsBytes:score.length});
    else{assert.deepEqual([...cfg],expected.config);assert.equal(sha(score),expected.scoreSemanticsSha256);}
    step('passed');passed=true;break;
   }
   assert(actions.length<50,'bounded menu actions');
  }
  await new Promise(r=>setTimeout(r,1));
 }
 assert(passed,'menu/config case did not finish: '+phase);
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){put('before-close.json',{phase,menu:words('menu_state',10)});c.close();closed=true;
  const until=performance.now()+65000;while(platform.timers.size&&performance.now()<until)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={terminal:true,pid:process.pid,mode,passed:passed&&!exception&&retired&&!errors.length,frames,phase,exception,errors,closed,retired,actions,checkpoints,workers,physicalWorkers:physical,sourceWasmSha256:sha(bytes),driverSha256:sha(readFileSync(resolve(out,'executed-driver.mjs'))),elapsedSeconds:(performance.now()-began)/1000,ordinaryMenuConfigChanges:true,hostSaveBoundary:true,reopenScoreSemanticsChecked:mode==='reopen',graphicsRecordingOnly:true,browserUiAccepted:false,ordinaryScoreProgressionAccepted:false,completeGame:false};
put('platform.json',summary);put('report.json',report);
put('saved-files.json',readdirSync(save,{recursive:true,withFileTypes:true}).filter(e=>e.isFile()).map(e=>{const name=resolve(e.parentPath,e.name),b=readFileSync(name);return{name,bytes:b.length,sha256:sha(b)};}));
console.log(JSON.stringify({mode,passed:report.passed,phase,frames,exception,retired,seconds:report.elapsedSeconds}));if(!report.passed)process.exitCode=1;
