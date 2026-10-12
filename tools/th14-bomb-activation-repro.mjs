// Diagnostic against the actual session and retail archive. No stock, power,
// enemies or player state is topped up. This is not a native-equivalence proof.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const wasm=readFileSync('artifacts/th14/end-session-check/end-session.wasm');
const {instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync('runtimes/th14/target.json','utf8'));
const data=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open_archive(p,data.length),1);
const error=()=>{const m=new Uint8Array(c.memory.buffer),s=c.error();return new TextDecoder().decode(m.subarray(s,m.indexOf(0,s)));};
const rows=[];
for(let character=0;character<3;character++)for(let subtype=0;subtype<2;subtype++){
 assert.equal(c.begin_selection(character,subtype),1,error());
 for(let n=0;n<180;n++)assert.equal(c.tick(0),1,error());
 const before=c.value(16),ok=c.tick(2);
 const row={character,subtype,frame:c.value(12),beforeBombs:before,afterBombs:c.value(16),active:c.value(36),bombError:c.value(37),script:c.value(38),opcode:c.value(39),updateReturned:ok,sessionError:error()};
 if(ok&&row.active){let ticks=0,followupOk=1;for(;ticks<2400;ticks++){followupOk=c.tick(0);if(!followupOk)break;}
  row.followup={ticks,updateReturned:followupOk,frame:c.value(12),active:c.value(36),sessionError:error()};}
 rows.push(row);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={date:'2026-10-09',diagnostic:true,completeGame:false,rows,wasmSha256:sha(wasm),archiveSha256:sha(data),scope:'Production GameSession, default Normal stage 1, six original character/weapon resources, 180 natural ticks then one held Bomb tick. Activated branches run up to 2400 further natural ticks. Records activation/runtime failures instead of counting HUD render or stock-only callback fixtures as actual Bomb support. Marisa A still runs an inherited, incorrect TH11 animation/effect path; removing the TH14 damage-collector refusal does not verify that weapon.',sourceHashes:Object.fromEntries(['cpp/game/BombController.cpp','cpp/game/BombController.hpp','cpp/game/ShotTh14.cpp','cpp/game/ShotManager.cpp','cpp/game/GameBattle.cpp','cpp/game/PlayerFrame.cpp','tests/cpp/th14-end-session-fixture.cpp'].map(s=>[s,sha(readFileSync('runtimes/th12/th12_web/'+s))]))};
writeFileSync('artifacts/th14/bomb-activation-repro.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(rows,null,2));
