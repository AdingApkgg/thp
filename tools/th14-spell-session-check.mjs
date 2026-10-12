import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const table=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-menu-table-native.json'),'utf8')),rows=[];
const tick=held=>{assert.equal(c.tick(held),1,string(c.error()));assert.equal(c.draw(),1,string(c.error()));};
const observe=()=>[c.value(0),...Array.from({length:10},(_,i)=>c.spell_session_value(i)).filter((_,i)=>i!==6),...Array.from({length:9},(_,i)=>c.replay_observation(10+i)).filter((_,i)=>i!==3&&i!==4),...Array.from({length:9},(_,i)=>c.player_diagnostic(i))];
for(let selection=0;selection<6;++selection)for(const [id,stage] of [[0,1],[26,3],[119,7]]){
 const row={selection,id,stage,error:''};rows.push(row);
 try{
  assert.equal(c.spell_session_begin(stage,id,selection,table.difficulty[id]),1,string(c.error()));for(let n=0;n<60;++n)tick(0);
  const before=observe();assert.equal(c.spell_session_pause(),1);assert.equal(c.phase(),2);for(let n=0;n<12;++n)tick(0);assert.deepEqual(observe().slice(0,10),before.slice(0,10),'paused battle state');
  tick(256);for(let n=0;n<13;++n)tick(0);assert.equal(c.phase(),1,'resume');assert.equal(c.spell_session_value(0),id);
  assert.equal(c.spell_session_result(0x80),1);tick(0);assert.equal(c.phase(),3);assert.deepEqual([c.spell_session_end_value(2),c.spell_session_end_value(3),c.spell_session_end_value(4)],[1,id,0]);
  for(let n=0;n<12;++n)tick(0);assert.equal(c.spell_session_end_value(1),2,'failure selects retry');tick(1);for(let n=0;n<13;++n)tick(0);assert.equal(c.phase(),1,'retry');assert.deepEqual(Array.from({length:7},(_,i)=>c.spell_session_value(i)),[id,0,0,400,id,32,2]);row.retry=true;
  assert.equal(c.spell_session_begin(stage,id,selection,table.difficulty[id]),1);const frames=[];for(let n=0;n<150;++n){tick(0);assert.equal(c.phase(),1);frames.push(observe());}
  assert.equal(c.spell_session_save(),1,'real recorder save');assert.equal(c.spell_session_replay(),1,string(c.error()));assert.deepEqual(Array.from({length:3},(_,i)=>c.spell_session_replay_value(i)),[2,id,id]);
  for(let n=0;n<frames.length;++n){tick(0);assert.equal(c.phase(),1);assert.deepEqual(observe(),frames[n],`replay frame ${n+1}`);}row.replayedFrames=frames.length;
  tick(0);assert.ok(c.phase()===4||c.phase()===0,'terminal marker returns/finishes replay');row.replayEnd=c.phase();
  assert.equal(c.spell_session_begin(stage,id,selection,table.difficulty[id]),1);for(let n=0;n<60;++n)tick(0);assert.equal(c.spell_session_result(0),1);tick(0);assert.equal(c.phase(),3);assert.deepEqual([c.spell_session_end_value(2),c.spell_session_end_value(3),c.spell_session_end_value(4)],[0,id,1]);for(let n=0;n<12;++n)tick(0);assert.equal(c.spell_session_end_value(1),0,'completed selects title');row.completedDispatch=true;
 }catch(e){row.error=e.message;console.log(JSON.stringify(row));break;}
 console.log(JSON.stringify(row));
}
const sha=b=>createHash('sha256').update(b).digest('hex'),passed=rows.length===18&&rows.every(r=>!r.error);writeFileSync(resolve(root,'docs/porting/th14-spell-session-verified.json'),JSON.stringify({passed,completeGame:false,nativeEquivalent:false,rows,wasmSha256:sha(bytes),scope:'Production integration with original resources: six loadouts x three representative SpellPr cards, pause/resume, controlled failure and actual Retry, real ReplayRecorder encoding/Replay decoding with 150-frame compared spell/player/economy/control state and terminal marker, controlled completion dispatch without capture. Visual animation RNG is unrecorded and excluded. No artificial invulnerability/firepower; not natural capture, original replay-frame equality, complete combat state, end-menu name/save UI, GPU or full-game equivalence.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/cpp/game/PauseEnd.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-spell-session-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');if(!passed)process.exitCode=1;else console.log('PASS 18 SpellPr pause/retry/replay/result routes');
