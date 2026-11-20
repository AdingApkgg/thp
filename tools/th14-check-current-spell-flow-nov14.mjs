import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {Th14WasiStagePool} from './th14-wasi-stage-pool-observer-clock-nov07.mjs';
import {beginTh14ProcessClockResolution} from './th14-process-clock-resolution-nov06.mjs';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/current-concurrent-mixer-nov14/spell-practice-flow');
const O=resolve(H,'current-v5');mkdirSync(O);mkdirSync(resolve(O,'save'));mkdirSync(resolve(O,'save/replay'));
const sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(readFileSync(p));
const build=load(resolve(H,'build.json')),bytes=readFileSync(resolve(H,'candidate.wasm'));assert.equal(sha(bytes),build.moduleSha256);
const earned=load(resolve(R,'docs/porting/th14-ordinary-normal-loadouts-nov14.json')).cases.find(c=>c.key==='reimub-normal');
const earnedSave=readFileSync(resolve(R,earned.writer,'save/scoreth14.dat'));assert.equal(sha(earnedSave),earned.encodedSha256);
writeFileSync(resolve(O,'save/scoreth14.dat'),earnedSave);
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
let created=false,closed=false,exception=null,finished=false,updates=0;
const actions=[],checkpoints=[];
const snapshot=label=>{const v={label,updates,menu:words('menu_state',10),selector:words('spell_selector_state',10),mode:words('mode_state',16),behavior:words('behavior_state',20),pause:words('pause_save_state',12)};checkpoints.push(v);put('progress.json',v);return v;};
async function step(n=1){for(let i=0;i<n;++i){assert(updates++<15000,'bounded menu flow');assert(c.frame(1/60),error());assert.equal(errors.length,0,errors.join('\n'));if(i%8===0)await new Promise(r=>setTimeout(r,1));}}
async function until(label,predicate,limit=2500){for(let i=0;i<limit;++i){if(predicate())return snapshot(label);await step();}throw Error(label+' timeout '+JSON.stringify(snapshot(label+'-timeout')));}
async function pulse(mask,label){actions.push({updates,mask,label});c.set_menu_input(mask);await step(2);c.set_menu_input(0);await step(10);}
const menuReady=(screen)=>{const m=words('menu_state',10);return m[0]===screen&&m[1]===2;};
async function selectMenu(target,label){for(let i=0;i<12;++i){const m=words('menu_state',10);if(m[2]===target){await pulse(1,label+'-confirm');return;}await pulse(m[2]>target?16:32,label+'-move');}throw Error(label+' selector did not reach '+target);}
try{
 created=true;assert.equal(c.shot_snapshot_enable(0),1);assert.equal(c.begin(initial.actualInitialTimeGetTimeInput,initial.actualOriginalSecurityCookie,0),1,error());
 await until('title-ready',()=>menuReady(1));
 await selectMenu(3,'spell-practice');
 await until('spell-stage-ready',()=>menuReady(17));
 if(words('mode_state',16)[14]===0)await pulse(128,'reimu-b-loadout');
 assert.equal(words('mode_state',16)[14],1,'earned Reimu B loadout');
 await selectMenu(0,'stage-one');await until('spell-row-ready',()=>menuReady(18));
 await selectMenu(0,'unseen-hard-lunatic-row');await step(30);assert(menuReady(18),'unseen row stays locked');snapshot('unseen-row-remains-locked');
 await selectMenu(1,'first-normal-boss-spell');await until('spell-difficulty-ready',()=>menuReady(19));
 assert.equal(words('spell_selector_state',10)[6]>>>31,0,'Normal spell genuinely seen in earned save');
 await selectMenu(1,'normal-spell');
 const first=await until('spell-first-player',()=>{const m=words('mode_state',16),b=words('behavior_state',20);return m[0]===1&&m[4]<120&&b[8]!==0xffffffff;});
 assert.deepEqual(first.mode.slice(1,4),[1,0,1]);assert.deepEqual(first.mode.slice(9,12),[0,0,400]);
 const spellId=first.mode[4];
 await step(120);c.press_pause();await until('spell-paused',()=>words('mode_state',16)[0]===2&&words('pause_save_state',12)[0]===3);
 await pulse(0x200000,'native-retry-shortcut');
 const retry=await until('spell-retry-first-player',()=>{const m=words('mode_state',16),b=words('behavior_state',20);return m[0]===1&&m[4]===spellId&&b[8]!==0xffffffff&&b[5]<first.behavior[5]+60;});
 assert.deepEqual(retry.mode.slice(1,5),[1,0,1,spellId]);assert.deepEqual(retry.mode.slice(9,12),[0,0,400]);
 await step(45);c.press_pause();await until('retry-paused',()=>words('mode_state',16)[0]===2&&words('pause_save_state',12)[0]===3);
 await pulse(0x10000,'native-title-shortcut');const returned=await until('spell-returned-main',()=>menuReady(1));assert.equal(returned.menu[2],3,'spell practice remains selected at title');
 await selectMenu(3,'reopen-spell-practice');await until('spell-selector-restored',()=>menuReady(19));
 const restored=words('spell_selector_state',10);assert.equal(restored[4],1);assert.equal(restored[6],spellId);
 await pulse(2,'cancel-difficulty');await until('back-spell-row',()=>menuReady(18));
 await pulse(2,'cancel-spell-row');await until('back-spell-stage',()=>menuReady(17));
 await pulse(2,'cancel-spell-stage');await until('back-main',()=>menuReady(1));
 await selectMenu(0,'ordinary-start');await until('ordinary-difficulty',()=>menuReady(5));
 await selectMenu(1,'ordinary-normal');await until('ordinary-character',()=>menuReady(6));
 // Character and weapon selectors use horizontal arrows.
 let m=words('menu_state',10);while(m[2]!==0){await pulse(64,'ordinary-reimu');m=words('menu_state',10);}await pulse(1,'ordinary-character-confirm');
 await until('ordinary-weapon',()=>menuReady(7));m=words('menu_state',10);while(m[2]!==1){await pulse(128,'ordinary-b');m=words('menu_state',10);}await pulse(1,'ordinary-weapon-confirm');
 const ordinary=await until('ordinary-first-player',()=>{const m=words('mode_state',16),b=words('behavior_state',20);return m[0]===1&&b[8]!==0xffffffff;});
 assert.deepEqual(ordinary.mode.slice(1,5),[1,0,0,0xffffffff]);assert.deepEqual(ordinary.mode.slice(9,12),[2,3,100]);assert.equal(ordinary.mode[5],0);
 assert.equal(c.flush_save(),1,'normal save interface');snapshot('mode-flow-saved');
 finished=true;
}catch(e){exception=String(e?.stack??e);}
finally{
 try{if(created){c.close();closed=true;const deadline=performance.now()+65000;while(platform.timers.size&&performance.now()<deadline)await new Promise(r=>setTimeout(r,5));assert.equal(platform.timers.size,0);}}
 catch(e){exception??=String(e?.stack??e);}
 await Promise.all(pools.map(p=>p.shutdown()));await platform.closeServices();clock.close();
}
const summary=platform.summary(),workers=pools.flatMap(p=>p.summary()),physical=pools.flatMap(p=>p.physicalSummary());
const retired=closed&&!['window','context','stream','pendingTimers','openFiles','liveDeclaredGpuFences'].some(k=>summary[k])&&Object.values(summary.liveObjects).every(n=>n===0)&&workers.every(w=>w.returned&&!w.error)&&physical.every(w=>w.closed&&w.exitCode===0)&&!clock.state.active;
const report={finished,exception,errors,retired,updates,actions,checkpoints,moduleSha256:sha(bytes),earnedSaveSha256:sha(earnedSave),gameplayUnitsRecompiled:0,onlyExistingMenuAndPauseInputs:true,silentMemoryAudio:true,graphicsRecordingOnly:true,browserAccepted:false,completeGame:false};
put('platform.json',summary);put('report.json',report);console.log(JSON.stringify({finished,exception,retired,updates,checkpoints:checkpoints.map(p=>p.label)}));
if(exception||errors.length||!retired||!finished)process.exitCode=1;
