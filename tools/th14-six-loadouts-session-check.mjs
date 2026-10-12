// Actual archive integration, with explicitly controlled power and invulnerability.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const wasm=readFileSync('artifacts/th14/end-session-check/end-session.wasm'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8')),data=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open_archive(p,data.length),1);
const error=()=>{const m=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(m.subarray(p,m.indexOf(0,p)));};const rows=[];
const sheets=JSON.parse(readFileSync('artifacts/th14/sht-native.json','utf8'));
for(let selection=0;selection<6;selection++)for(const focused of [false,true])for(const power of [100,200,300,400]){
 assert.equal(c.begin_selection(Math.floor(selection/2),selection%2),1,error());assert.equal(c.diagnostic_power(power),1,error());let draws=0,maxShots=0,maxHoming=0,maxDelayed=0,maxFocused=0;
 for(let frame=0;frame<1200;frame++){
  assert.equal(c.diagnostic_power(power),1,error());assert.equal(c.diagnostic_shot_tick(1|(focused?8:0)),1,`${selection}/${focused}/${power}/${frame}: ${error()}`);assert.equal(c.value(0),1);
  maxHoming=Math.max(maxHoming,c.shot_observation(14));maxDelayed=Math.max(maxDelayed,c.shot_observation(15));maxFocused=Math.max(maxFocused,c.shot_observation(16));maxShots=Math.max(maxShots,c.shot_observation(17));
  assert.ok(c.shot_observation(16)<=1,'cached type-2 shot must not be duplicated');
  if(frame%30===0){assert.equal(c.draw(),1,error());draws++;}
 }
 const group=sheets.files[selection].groups[power/100+(focused?5:0)];
 const expectsDelayed=group.records.some(hex=>{const b=Buffer.from(hex,'hex');return b.readUInt32LE(0x2c)===0x4538f0&&b.readInt32LE(0x38)>=0;});
 const row={selection,focused,power,frames:1200,draws,maxShots,maxHoming,maxDelayed,maxFocused,expectsDelayed};rows.push(row);console.log(JSON.stringify(row));assert.ok(maxShots>0);if(expectsDelayed)assert.ok(maxDelayed>0,'retail sheet requests a delayed upward turn');
}
assert.ok(rows.filter(r=>r.selection===0&&r.focused).every(r=>r.maxFocused===1),'Reimu A focused persistent shot must be present');
assert.ok(rows.filter(r=>r.selection<2&&!r.focused).every(r=>r.maxHoming>0),'Reimu homing shots must acquire actual stage enemies');
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync('docs/porting/th14-six-loadouts-session-verified.json',JSON.stringify({passed:true,nativeEquivalent:false,completeGame:false,rows,archiveSha256:sha(data),wasmSha256:sha(wasm),scope:'Six actual retail SHT/ANM loadouts in Normal stage 1, focused/unfocused and power 100/200/300/400, 1200 frames each and graphics submissions. Power and invulnerability are diagnostic controls. Observes populated shot pools, actual-enemy homing acquisition, type-2 no-duplicate gate/persistent shot, and Sakuya B delayed option turns. Independent native component reports cover arithmetic; this integration does not prove native call order, natural survival, whole campaign, sound playback, replay or GPU pixels.',sourceHashes:Object.fromEntries(['cpp/game/ShotManager.cpp','cpp/game/ShotManager.hpp','cpp/game/ShotTh14.cpp','cpp/game/PlayerFrame.cpp','cpp/game/ShtResource.cpp','tests/cpp/th14-end-session-fixture.cpp'].map(s=>[s,sha(readFileSync('runtimes/th12/th12_web/'+s))]))},null,2)+'\n');console.log('PASS: six loadouts, 57,600 actual archive frames.');
