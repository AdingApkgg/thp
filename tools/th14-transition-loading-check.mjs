// Original resources, injected native completion request, ordinary collisions.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);const cases=[];
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/transition-control-native.json'),'utf8'));
assert.equal(native.passed,true);assert.equal(native.rows.length,480);
assert.equal(native.musicRows.length,392);
assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const musicBoundaries=[];
for(const stage of [1,6]){
 assert.equal(c.stage_music_begin(stage,299),1);
 for(let tick=0;tick<3;++tick){assert.equal(c.tick(0),1);assert.equal(c.draw(),1);assert.equal(c.stage_music_events(1),0,'no legacy stage-six clock300 resume event in TH14');assert.equal(c.stage_music_events(0),0);musicBoundaries.push({stage,controlFrame:299+tick,resumeEvents:0});}
}
const gate=(timer,frame,flags=0)=>native.rows.find(r=>r.oldBackground===1&&r.hudFlags===0x100&&r.resultTimer===timer&&r.controlFrame===frame&&r.controlFlags===flags);
assert.equal(gate(119,0).gated,true);assert.equal(gate(120,0).gated,false);
assert.ok(gate(120,0).calls.some(c=>c.service==='background_overlap'));
assert.equal(gate(120,29,0x800).activated,false);assert.equal(gate(120,30,0x800).activated,true);
const world=()=>Array.from({length:14},(_,i)=>c.transition_state(i));const gameRng=()=>[c.deferred_state(2),c.deferred_state(3)];
for(let selection=0;selection<6;++selection)for(let next=2;next<=6;++next)for(const delay of [0,9,44]){
 assert.equal(c.transition_begin(next,selection),1,`selection${selection} next${next}`);assert.equal(c.phase(),6);assert.equal(c.value(0),0);assert.equal(c.value(1),next);assert.equal(c.deferred_templates(),0);const saved=world(),rng=gameRng(),jobs=c.deferred_job_count();assert.deepEqual(saved.slice(0,2),[1,1]);assert.equal(saved[6],next);
 for(let frame=0;frame<delay+jobs;++frame){assert.equal(c.loading_tick(),1);assert.equal(c.tick(0x101),1);assert.equal(c.draw(),1);assert.equal(c.phase(),6);assert.equal(c.value(0),0);assert.deepEqual(world(),saved,'existing world/player/economy and clocks held until resource readiness');assert.deepEqual(gameRng(),rng,'gameplay RNG held while loaders update');if(frame>=delay)assert.equal(c.deferred_job(frame-delay),1);}
 assert.equal(c.deferred_finish(),1);assert.equal(c.phase(),1);assert.equal(c.value(0),1);assert.deepEqual(world().slice(0,2),[1,1]);assert.equal(c.transition_state(6),0);assert.equal(c.transition_state(4),0);assert.equal(c.transition_state(5),1);assert.equal(c.transition_state(2),0);assert.equal(c.transition_state(3),0);
 let frames=0;while(!c.transition_state(4)&&frames<300){assert.equal(c.tick(0),1);assert.equal(c.draw(),1);++frames;
  // Native gates plus the observed production result timer=1 at loading exit.
  // Timer stepping itself belongs to the caller and is not a native oracle here.
  const expectedClock=frames<120?0:frames<150?frames-119:1;
  assert.deepEqual([c.transition_state(2),c.transition_state(3),c.transition_state(4)],[expectedClock,expectedClock,frames>=150?1:0],`native120/30 gate boundaries at tick${frames}`);
  assert.equal(c.stage_music_events(0),frames===150?1:0,'music starts once at actual stage activation');assert.equal(c.stage_music_events(1),0);
 }assert.equal(frames,150);assert.ok(c.transition_state(4),'existing controller activates the prepared next stage');assert.deepEqual(world().slice(0,2),[1,1]);cases.push({selection,next,delay,jobs,activationFrames:frames});
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-transition-loading-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases,wasmSha256:sha(bytes),nativeExecutableSha256:native.executableSha256,nativeControlGateCases:native.rows.length,nativeMusicCallbackCases:native.musicRows.length,musicBoundaries,scope:'Ninety original-resource existing-world stage entries: six loadouts, next stages2..6, delays0/9/44 plus real resource jobs. Injected dialogue-stage-complete request, ordinary collisions with no invincibility or added power. Existing battle/player/economy/gameplay RNG and clocks held while loading-family ANMs update; incoming templates ready before retained-controller transition and eventual stage activation. 13500 production control-clock states follow the independently checked retail120/30 gate boundaries from the observed result-timer1 loading exit; caller timer stepping is outside the native oracle. Actual stage music event occurs once at activation; no legacy clock300 resume in stage1/6 boundaries. Main-thread cooperative GPU jobs; original thread/callback scheduling, all ANM/RNG streams, outgoing background and loading GPU pixels, natural stage clear and complete campaign equivalence excluded.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.hpp','runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-transition-loading-check.mjs','tools/th14-transition-control-native.py','artifacts/th14/transition-control-native.json'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${cases.length} delayed existing-world entries; player/economy retained until actual stage activation`);
