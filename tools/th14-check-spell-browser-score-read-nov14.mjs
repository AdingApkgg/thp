import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/current-concurrent-mixer-nov14/spell-browser-persistence');
const key=process.argv[2];assert(['before','after'].includes(key));const O=resolve(H,key);mkdirSync(O);mkdirSync(resolve(O,'save'));
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const source=load(resolve(H,'inputs.json'))[key],score=readFileSync(source.path);assert.equal(sha(score),source.sha256);writeFileSync(resolve(O,'save/scoreth14.dat'),score);
const buildRoot=resolve(H,'../spell-viewer-completion'),build=load(resolve(buildRoot,'build.json')),bytes=readFileSync(resolve(buildRoot,'candidate.wasm'));assert.equal(sha(bytes),build.sha256);
const native=resolve(R,'artifacts/th14/player-entry-end-menu-nov06/campaign'),initial=load(resolve(native,'untouched-first-player.json'));
copyFileSync(resolve(native,'work/appdata/ShanghaiAlice/th14/th14.cfg'),resolve(O,'save/th14.cfg'));
const archivePath=JSON.parse(readFileSync(resolve(R,'runtimes/th14/target.json'))).dataArchives['th14.dat'].path;
assert.equal(sha(readFileSync(archivePath)),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const music=load(resolve(R,'artifacts/th14/published-vorbis-cache-nov13/prepared.json')),musicDirectory=resolve(R,music.musicDirectory);
const put=(n,v)=>writeFileSync(resolve(O,n),JSON.stringify(v,null,2)+'\n');
writeFileSync(resolve(O,'executed-driver.mjs'),readFileSync(import.meta.filename));
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
let created=false,closed=false,exception=null,finished=false,updates=0,loaded=null;
try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 for(;updates<2500;++updates){const m=words('menu_state',10);if(m[0]===1&&m[1]===2)break;assert(c.frame(1/60),error());await new Promise(r=>setTimeout(r,1));}
 assert(updates<2500,'title loading readiness');assert.equal(c.observation_count(),0,'reader never starts gameplay');
 const size=c.score_semantics_size();assert.equal(size,149076);loaded=Buffer.from(new Uint8Array(memory.buffer,c.score_semantics_data(),size));writeFileSync(resolve(O,'score-observed.bin'),loaded);
 assert.equal(sha(readFileSync(source.path)),source.sha256,'source score never modified');finished=true;
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){c.close();closed=true;const deadline=performance.now()+65000;while(platform.timers.size&&performance.now()<deadline)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={key,finished,exception,errors,retired,updates,sourceSha256:source.sha256,loadedSha256:loaded?sha(loaded):null,loadedBytes:loaded?.length,moduleSha256:sha(bytes),noGameplayStarted:true,noLiveStateWrites:true,silentMemoryAudio:true,graphicsRecordingOnly:true,browserAccepted:false,completeGame:false};
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify(report));if(exception||errors.length||!retired||!finished)process.exitCode=1;
