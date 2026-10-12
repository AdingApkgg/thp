import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),path=resolve(root,'artifacts/th14/spell-timeout-session-check/timeout-session.wasm'),bytes=readFileSync(path);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),ptr=c.allocate(archive.length);new Uint8Array(c.memory.buffer,ptr,archive.length).set(archive);assert.equal(c.open_archive(ptr,archive.length),1);
const table=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-menu-table-native.json'),'utf8'));
const text=ptr=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(ptr,b.indexOf(0,ptr)));};
const timing=()=>Array.from({length:5},(_,n)=>c.timeout_state(n)>>>0);
// Record selected gameplay fields; visual RNG and ANM IDs are deliberately excluded.
const observe=()=>[...timing(),...[10,11,12,15,16,17,18].map(n=>c.replay_observation(n)>>>0),...Array.from({length:9},(_,n)=>c.player_diagnostic(n)>>>0)];
const rows=[];let comparedFrames=0;
outer:for(let selection=0;selection<6;++selection)for(const [id,stage] of [[0,1],[26,3]]){
 const row={selection,id,stage,error:''};rows.push(row);
 try{
  assert.equal(c.spell_session_begin(stage,id,selection,table.difficulty[id]),1,text(c.error()));const states=[];
  for(let frame=1;frame<=10000;++frame){assert.equal(c.combat_tick(1),1,text(c.error()));assert.equal(c.draw(),1,text(c.error()));assert.equal(c.timeout_clock(frame/60),1);states.push(observe());if(c.phase()!==1)break;}
  assert.equal(c.phase(),3,'actual ECL reaches end menu');assert.equal(c.spell_session_end_value(4),1,'actual defeat completes card');
  assert.equal(c.timeout_state(11),1,'capture recorded without forced result');assert.equal(c.timeout_state(4),1,'one completed time');
  row.frames=states.length;row.recordedTiming=timing();assert.equal(c.spell_session_save(),1,'actual completed replay save');
  assert.equal(c.spell_session_replay(),1,text(c.error()));assert.equal(c.timeout_state(8),row.recordedTiming[3],'decoded replay time');
  for(let frame=1;frame<=states.length;++frame){assert.equal(c.combat_tick(0),1,text(c.error()));assert.equal(c.draw(),1,text(c.error()));assert.equal(c.timeout_clock(100+frame/30),1);assert.deepEqual(observe(),states[frame-1],`selection${selection} card${id} replay frame${frame}`);++comparedFrames;}
  assert.equal(c.phase(),4,'completed replay returns finished');row.replayTiming=timing();row.phase=c.phase();
 }catch(e){row.error=e.message;row.final=timing();row.diagnostic=text(c.progression_diagnostic());console.log(JSON.stringify(row));break outer;}
 console.log(JSON.stringify(row));
}
const sha=b=>createHash('sha256').update(b).digest('hex'),passed=rows.length===12&&rows.every(r=>!r.error);
const fixture=resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-spell-timeout-session-fixture.cpp');
writeFileSync(resolve(root,'docs/porting/th14-spell-capture-replay-session-observed-oct11.json'),JSON.stringify({passed,completeGame:false,nativeEquivalent:false,combatIsolation:true,forcedInvincibility:true,extraFirepower:false,artificialClear:false,cases:rows.length,comparedFrames,rows,wasmSha256:sha(bytes),fixtureSha256:sha(readFileSync(fixture)),archiveSha256:sha(archive),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Two original SpellPr ECL cards x six loadouts, ordinary fire held and diagnostic invulnerability only. Actual enemy defeat/end callback records capture; no forced end/bonus/capture or synthetic power. Actual ReplayRecorder save/decode/playback compares selected gameplay/timing/player fields until original ECL completion. Replay clock deliberately uses a different supplied origin/rate to verify recorded timing substitution. No native combat, ordinary survival, complete state, visual RNG, browser/GPU/audio or entire-game equality claim.'},null,2)+'\n');
if(!passed)process.exitCode=1;else console.log(`PASS ${rows.length} isolated actual ECL capture/save/replay routes / ${comparedFrames} compared frames`);
