// Archive integration with controlled stock and invulnerability.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const wasm=readFileSync('artifacts/th14/end-session-check/end-session.wasm'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8')),data=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open_archive(p,data.length),1);
const error=()=>{const m=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(m.subarray(p,m.indexOf(0,p)));};const rows=[];
for(const focused of [false,true])for(const power of [40,80,120,160]){
 assert.equal(c.begin_selection(2,0),1,error());assert.equal(c.diagnostic_power(power),1,error());let draws=0,maxFlying=0,maxAttached=0,maxExploding=0,maxSlowed=0,maxCircles=0;
 for(let frame=0;frame<1200;frame++){
  assert.equal(c.diagnostic_power(power),1,error());assert.equal(c.diagnostic_shot_tick(1|(focused?8:0)),1,error());assert.equal(c.value(0),1);
  const [flying,attached,exploding,targets,slowed,totalCounter,attachedCounter,circles]=Array.from({length:8},(_,i)=>c.shot_observation(i+6));
  assert.equal(totalCounter,flying+attached+exploding,`type-5 count frame ${frame}`);assert.equal(attachedCounter,attached+exploding,`attached count frame ${frame}`);
  maxFlying=Math.max(maxFlying,flying);maxAttached=Math.max(maxAttached,attached);maxExploding=Math.max(maxExploding,exploding);maxSlowed=Math.max(maxSlowed,slowed);maxCircles=Math.max(maxCircles,circles);
  if(frame%30===0){assert.equal(c.draw(),1,error());draws++;}
 }
 const row={focused,power,frames:1200,draws,maxFlying,maxAttached,maxExploding,maxSlowed,maxCircles};rows.push(row);console.log(JSON.stringify(row));
}
assert.ok(rows.filter(r=>r.focused).every(r=>r.maxFlying&&r.maxAttached&&r.maxExploding&&r.maxSlowed&&r.maxCircles),'Focused Sakuya A must exercise flying, attached and exploding knives, enemy slowdown and expanding damage circles');
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync('docs/porting/th14-shot-sakuya-session-verified.json',JSON.stringify({passed:true,nativeEquivalent:false,completeGame:false,rows,archiveSha256:sha(data),wasmSha256:sha(wasm),scope:'Actual retail Sakuya A SHT/ANM/ECL in stage 1, focused/unfocused firing at controlled power 40/80/120/160, refreshed invulnerability. Checks per-frame total and attached counters against live type-5 shot phases, flying/attachment/explosion, enemy slowdown and positive-radius period-2 callback circles. Excludes natural gameplay, native flow equivalence, replay, audio and GPU pixels.',sourceHashes:Object.fromEntries(['cpp/game/ShotSakuyaTh14.cpp','cpp/game/ShotManager.cpp','cpp/game/ShotManager.hpp','cpp/game/ShotTh14.cpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyState.hpp','cpp/game/GameBattle.hpp','tests/cpp/th14-end-session-fixture.cpp'].map(s=>[s,sha(readFileSync('runtimes/th12/th12_web/'+s))]))},null,2)+'\n');console.log('PASS: Sakuya A archive firing integration.');
