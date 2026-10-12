import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);const rows=[];
const error=()=>{const p=c.error(),b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
for(let selection=0;selection<6;++selection)for(const continues of [0,1])for(const delay of [0,9,44]){
 assert.equal(c.ending_session_begin(selection,continues),1,error());let transition=0;
 while(c.phase()===1&&transition<500){assert.equal(c.combat_tick(0),1,error());assert.equal(c.draw(),1,error());++transition;}
 assert.equal(transition,380);assert.equal(c.phase(),5);assert.equal(c.ending_session_state(0),selection+(continues?7:1));assert.equal(c.ending_session_state(6),0);
 let frames=0;const jobs=[];
 while(c.phase()===5&&frames<30000){
  if(c.ending_session_state(1)){
   const frozen=[c.ending_session_state(3),c.ending_session_state(7)],before=c.ending_session_state(5),staff=!!c.ending_session_state(8);
   for(let wait=0;wait<delay;++wait){assert.equal(c.tick(513),1,error());assert.equal(c.draw(),1,error());assert.equal(c.phase(),5);assert.deepEqual([c.ending_session_state(3),c.ending_session_state(7)],frozen,'script clock and instruction held while actual ending/ANM callbacks continue');}
   assert.equal(c.ending_session_state(5),before+delay);assert.equal(c.ending_session_complete(),1,error());assert.equal(c.ending_session_state(1),0);jobs.push({staff,delay});
  }
  assert.equal(c.tick((frames%2?0:1)|512),1,error());assert.equal(c.draw(),1,error());++frames;
 }
 assert.equal(c.phase(),0,error());assert.equal(c.title_screen(),14);assert.deepEqual(jobs.map(x=>x.staff),continues?[false]:[false,true]);
 const menuTick=(held=0)=>{assert.equal(c.tick(held),1,error());assert.equal(c.draw(),1,error());};
 const menuWait=n=>{for(let i=0;i<n;++i)menuTick();},press=k=>{menuTick(k);menuTick();};
 menuWait(12);assert.equal(c.results_probe_value(10),1,'actual Results title100 is present');assert.equal(c.results_probe_value(12),1,'ascii19 name-entry root is present');
 if(c.results_probe_value(3)===0){press(1);press(16);press(64);}assert.equal(c.results_probe_value(3),90);press(1);menuWait(20);
 assert.equal(c.title_screen(),continues?1:15,'continued endings return to title; no-continue endings offer replay saving');
 if(!continues){assert.equal(c.results_probe_value(11),1,'actual ReplaySave title101 is present');press(2);menuWait(12);assert.equal(c.title_screen(),1);}
 rows.push({selection,continues,delay,transitionFrames:transition,endingFrames:frames,jobs,scoreNameCompleted:true,replaySaveOffered:!continues,returnedToMain:true});
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-ending-loading-session-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,rows,wasmSha256:sha(bytes),scope:'Thirty-six actual GameSession stage6 completion/ending/staff/result routes with original resources, six loadouts, continued/uncontinued endings and resource delays0/9/44. Artificial completion boundary and controlled invulnerability during the380-frame ending-entry wait; not a natural campaign. Each actual opcode7 resource stays undecoded until its job; uncontinued endings also load staff, while original continued scripts finish without staff; script clock/instruction held, ending callback/animation/draw continue, then actual resources/templates activate and reach Results. Completes actual keyboard name entry, validates title100/ascii19, continued ending returns to Main directly, no-continue ending offers title101 ReplaySave then cancels back to Main. GPU/audio, native thread scheduling and whole native ending equivalence excluded.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/Ending.cpp','runtimes/th12/th12_web/cpp/game/Ending.hpp','runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/TitleResults.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-ending-loading-session-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${rows.length} deferred original ending/staff/result/name/replay-choice/title routes; ${rows.reduce((n,r)=>n+r.jobs.length,0)} actual resource jobs`);
