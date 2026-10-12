// Actual archive/session shooting and Bomb integration. No native equivalence claim.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const wasm=readFileSync('artifacts/th14/end-session-check/end-session.wasm'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8')),data=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open_archive(p,data.length),1);
const error=()=>{const m=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(m.subarray(p,m.indexOf(0,p)));};const rows=[];
for(const focused of [false,true]){
 assert.equal(c.begin_selection(1,0),1,error());let ticks=0,draws=0;const transitions=[];let previous=-1,bombStarted=false,bombEnded=false;
 for(;ticks<2400&&c.value(0)===1;ticks++){
  const held=(focused?8:0)|(ticks===180?2:0);assert.equal(c.tick(held),1,`${focused} ${ticks}: ${error()}`);
  if(ticks%30===0){assert.equal(c.draw(),1,error());draws++;}
  if(ticks===180){assert.equal(c.value(16),2,'activation consumes one Bomb');assert.equal(c.value(36),1);bombStarted=true;}
  if(ticks>180&&c.value(36)===0)bombEnded=true;
  const state=c.value(26);if(state!==previous){transitions.push({frame:c.value(12),state,lives:c.value(14),power:c.value(18),options:c.value(30)});previous=state;}
 }
 assert.ok(bombStarted&&bombEnded);assert.ok(transitions.some(t=>t.state===2),'natural death must be exercised');assert.ok(transitions.some(t=>t.state===0&&t.frame>180),'natural respawn must be exercised');
 rows.push({focused,ticks,draws,lastFrame:c.value(12),phase:c.value(0),bombStarted,bombEnded,transitions});
 console.log(`PASS: Marisa A ${focused?'focused':'unfocused'} Bomb integration, ${ticks} actual session ticks.`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync('docs/porting/th14-marisa-a-session-verified.json',JSON.stringify({passed:true,completeGame:false,rows,archiveSha256:sha(data),wasmSha256:sha(wasm),scope:'Production GameSession with retail archive and default Normal stage 1, Marisa A focused/unfocused without firing, Bomb at tick 180 then continued stage through natural hit/death/respawn or game over, recording graphics submissions every 30 ticks. No stock/power/state top-up. Diagnostic integration pass, not a native-equivalence or GPU-pixel proof.',sourceHashes:Object.fromEntries(['cpp/game/GameSession.cpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp','cpp/game/BombController.cpp','cpp/game/PlayerMotion.cpp','cpp/game/PlayerFrame.cpp','cpp/game/ShotManager.cpp','cpp/game/ShotManager.hpp','cpp/game/ShotTh14.cpp','tests/cpp/th14-end-session-fixture.cpp'].map(s=>[s,sha(readFileSync('runtimes/th12/th12_web/'+s))]))},null,2)+'\n');
