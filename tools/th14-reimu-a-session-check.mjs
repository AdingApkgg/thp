import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const wasm=readFileSync('artifacts/th14/end-session-check/end-session.wasm'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8')),data=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open_archive(p,data.length),1);
const error=()=>{const m=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(m.subarray(p,m.indexOf(0,p)));};const rows=[];
const float=b=>new Float32Array(new Uint32Array([b]).buffer)[0];
for(const focused of [false,true])for(const firing of [false,true]){
 assert.equal(c.begin_selection(0,0),1,error());let ticks=0,draws=0,ended=false,minX=Infinity,maxX=-Infinity,maxShift=0,areaSamples=0;const periods=new Set(),positions=new Set(),liveAreas=new Set();
 for(;ticks<2400&&c.value(0)===1;ticks++){
  assert.equal(c.tick((focused?8:0)|(firing?1:0)|(ticks===180?2:0)),1,`${focused} ${firing} ${ticks}: ${error()}`);
  if(ticks%30===0){assert.equal(c.draw(),1,error());draws++;}
  if(ticks===180){assert.equal(c.value(16),2);assert.equal(c.value(36),1);assert.equal(c.reimu_observation(0),1);for(let i=0;i<4;i++){assert.equal(c.reimu_observation(11+i*8),300);assert.equal(c.reimu_observation(12+i*8),2);}}
  if(c.value(36)&&ticks>=180){minX=Math.min(minX,float(c.reimu_observation(2)));maxX=Math.max(maxX,float(c.reimu_observation(2)));maxShift=Math.max(maxShift,Math.abs(float(c.reimu_observation(3))));let alive=0;
   for(let i=0;i<4;i++){const flags=c.reimu_observation(5+i*8);alive+=flags&1;assert.ok(flags&4);periods.add(c.reimu_observation(6+i*8));positions.add(`${c.reimu_observation(7+i*8)},${c.reimu_observation(8+i*8)},${c.reimu_observation(9+i*8)}`);++areaSamples;}
   liveAreas.add(alive);
  }
  if(ticks>180&&c.value(36)===0){assert.equal(c.reimu_observation(0),0);assert.equal(c.reimu_observation(4)&4,0);ended=true;}
 }
 const row={focused,firing,ticks,draws,ended,minX,maxX,maxShift,areaSamples,periods:[...periods],liveAreas:[...liveAreas],distinctAreaTransforms:positions.size,phase:c.value(0)};rows.push(row);console.log(JSON.stringify(row));
 assert.ok(ended);assert.ok(periods.has(1)&&periods.has(10));assert.ok(liveAreas.has(4)&&liveAreas.has(1));assert.ok(positions.size>8,'animation/history must produce multiple transforms');assert.ok(maxShift>=12&&maxX>minX+20);
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync('docs/porting/th14-reimu-a-session-verified.json',JSON.stringify({passed:true,nativeEquivalent:false,completeGame:false,rows,archiveSha256:sha(data),wasmSha256:sha(wasm),scope:'Actual default Normal stage-1 retail GameSession, Reimu A focused/unfocused and firing/not firing, Bomb at tick 180, no stock/power/invulnerability top-up. Checks stock consumption, four 300-damage callback areas, native period changes, staggered expiry, varied animation-driven transforms, automatic lateral displacement, >=250 finish and flag cleanup, and graphics submissions. Excludes native call-order, GPU pixels, undefined native polar z and later-stage laser consumers.',sourceHashes:Object.fromEntries(['cpp/game/GameSession.cpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp','cpp/game/BombController.cpp','cpp/game/BombController.hpp','cpp/game/ShotTh14.cpp','cpp/game/ShotManager.hpp','cpp/game/PlayerMotion.cpp','cpp/game/PlayerFrame.cpp','tests/cpp/th14-end-session-fixture.cpp'].map(s=>[s,sha(readFileSync('runtimes/th12/th12_web/'+s))]))},null,2)+'\n');console.log('PASS: Reimu A actual archive Bomb integration.');
