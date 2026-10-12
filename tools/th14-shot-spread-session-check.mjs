// Retail resource integration with controlled power and invulnerability.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const wasm=readFileSync('artifacts/th14/end-session-check/end-session.wasm'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8')),data=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open_archive(p,data.length),1);
const error=()=>{const m=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(m.subarray(p,m.indexOf(0,p)));};
assert.equal(c.begin_selection(0,0),1,error());const callbacks=Array.from({length:6},(_,selection)=>({selection,masks:[0,1,2].map(k=>c.shot_callbacks(selection,k))}));console.log('Retail callback masks:',JSON.stringify(callbacks));const rows=[];
for(const selection of callbacks.filter(r=>(r.masks[0]|r.masks[2])&16).map(r=>r.selection))for(const focused of [false,true])for(const power of [40,80,120,160]){
 assert.equal(c.begin_selection(selection>>1,selection&1),1,error());assert.equal(c.diagnostic_power(power),1,error());let ticks=0,draws=0,maxSpread=0,maxHit=0,maxMoving=0,maxBeams=0,maxBeamHits=0,maxPanEvents=0,failure='';
 for(;ticks<1200&&c.value(0)===1;ticks++){
  assert.equal(c.diagnostic_power(power),1,error());
  if(!c.diagnostic_shot_tick(1|(focused?8:0))){failure=error();break;}
  maxSpread=Math.max(maxSpread,c.shot_observation(0));maxHit=Math.max(maxHit,c.shot_observation(1));maxMoving=Math.max(maxMoving,c.shot_observation(2));
  maxBeams=Math.max(maxBeams,c.shot_observation(3));maxBeamHits=Math.max(maxBeamHits,c.shot_observation(4));maxPanEvents=Math.max(maxPanEvents,c.shot_observation(5));
  if(ticks%30===0){if(!c.draw()){failure=error();break;}draws++;}
 }
 const row={selection,focused,power,ticks,draws,maxSpread,maxHit,maxMoving,maxBeams,maxBeamHits,maxPanEvents,failure};rows.push(row);console.log(JSON.stringify(row));
}
const sha=b=>createHash('sha256').update(b).digest('hex');const passed=rows.length>0&&rows.every(r=>!r.failure)&&rows.some(r=>r.maxSpread>0)&&rows.some(r=>r.maxMoving>0)&&rows.filter(r=>!r.focused).every(r=>r.maxBeams>0&&r.maxBeams<=r.power/40&&r.maxBeamHits>0&&r.maxPanEvents>0);
writeFileSync('docs/porting/th14-shot-spread-session-verified.json',JSON.stringify({passed,nativeEquivalent:false,completeGame:false,callbacks,rows,archiveSha256:sha(data),wasmSha256:sha(wasm),scope:'Actual retail SHT/ANM/ECL session, selections requiring spawn/hit callback 4, focused/unfocused firing with controlled power 40/80/120/160 and refreshed invulnerability. Records spread projectiles, hit state and live moving-circle areas, active beams bounded by option count, actual beam hits and current-voice pan delivery requests. No natural gameplay, complete-game, native-equivalence or GPU-pixel claim.',sourceHashes:Object.fromEntries(['cpp/game/ShotManager.cpp','cpp/game/ShotManager.hpp','cpp/game/ShotTh14.cpp','cpp/game/ShotCallbacksTh14.cpp','cpp/game/ShotDamageTh14.cpp','cpp/game/ShotDamageTh14.hpp','tests/cpp/th14-end-session-fixture.cpp'].map(s=>[s,sha(readFileSync('runtimes/th12/th12_web/'+s))]))},null,2)+'\n');assert.ok(passed,'Retail firing integration must exercise spread and a live moving circle without a failure');console.log('PASS: actual archive spread/explosion firing integration.');
