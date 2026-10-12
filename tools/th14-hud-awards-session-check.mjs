import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-awards-session-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-awards-session-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),path=resolve(out,'awards-session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-awards-text-native.json'),'utf8'));
const scenarios=[
 {result:1,time:0,show:0,bonus:3000000,frames:60,encoded:2206633,alpha:255},
 {result:0,time:2,show:1,bonus:3000000,frames:60,encoded:24118632,alpha:80},
 {result:1,time:2,show:1,bonus:3000000,frames:60000,encoded:102106533,alpha:255},
 {result:1,time:2,show:1,bonus:3000000,frames:59,encoded:0,alpha:0},
 {result:0,time:3,show:1,bonus:3000000,frames:60,encoded:24118632,alpha:255},
 {result:1,time:2,show:0,bonus:3000000,frames:60,encoded:24118632,alpha:255},
 {result:3,time:0,show:0,bonus:-1,frames:60,encoded:2206633,alpha:255}
];
// The native corpus owns the encoded values and expected text, rather than
// deriving expected decode/grouping from the production implementation.
for(const s of scenarios){const n=native.rows.find(r=>Object.entries(s).every(([k,v])=>r[k]===v)&&r.manager===1);assert.ok(n,JSON.stringify(s));s.native=n;}
const bits=x=>{const b=new ArrayBuffer(4);new Float32Array(b)[0]=x;return new Uint32Array(b)[0];},text=ptr=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(ptr,b.indexOf(0,ptr)));};
let cases=0,submissions=0;const life=[];
for(let selection=0;selection<6;++selection){assert.equal(c.begin(1,selection>>1,selection&1,1),1,text(c.error()));
 for(const s of scenarios){assert.equal(c.awards_setup(s.result,s.time,s.show,s.bonus,s.frames,s.encoded,s.alpha),1);assert.equal(c.draw(),1,text(c.error()));assert.equal(c.awards_render_finite(),1);submissions+=c.awards_submissions();
  assert.equal(c.awards_count(),s.native.requests.length,`selection${selection} request count`);
  for(const [i,q] of s.native.requests.entries()){
   assert.equal(text(c.awards_bytes(i)),q.text);let x=q.position[0];if(q.horizontal===0)for(const ch of q.text)x-=ch===','?2:6;
   assert.deepEqual(Array.from({length:8},(_,k)=>c.awards_word(i,k)>>>0),[bits(x),bits(q.position[1]),bits(q.position[2]),q.color,q.font,q.passIndex,...q.scale.map(bits)]);
  }
  if(s.time===3&&s.show)assert.equal(c.awards_state(2),0,'actual Hud clears show flag after stale time VM');++cases;
 }
 assert.equal(c.awards_setup(1,2,1,3000000,60,24118632,255),1);assert.deepEqual([3,4,5,6].map(k=>c.awards_state(k)),[112,95,22,0]);
 // Advance the original ANM scripts alone to observe their actual retirement.
 // This is a resource lifecycle check, not a natural stage or spell clear.
 let timeGone=-1;for(let frame=0;frame<600;++frame){assert.equal(c.awards_animation_tick(),1);assert.equal(c.draw(),1,text(c.error()));if(!c.awards_state(1)){timeGone=frame+1;break;}}
 assert.ok(timeGone>0,'front95 eventually retires');assert.equal(c.awards_state(2),0);assert.equal(c.awards_count(),1,'only held stage result remains');life.push({selection,timeAnimationRetiredAt:timeGone});
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'tests/cpp/th14-session-fixture.cpp','cpp/game/GameBattle.cpp','cpp/game/GameSession.cpp','cpp/game/Hud.cpp','cpp/game/HudTh14Text.cpp','cpp/game/SpellTiming.cpp','cpp/game/HudTh14Notice.cpp','cpp/game/AsciiText.cpp','cpp/game/SceneSchedule.hpp'];
writeFileSync(resolve(root,'docs/porting/th14-hud-awards-session-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases,submissions,life,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Actual GameSession.begin/draw with original archive, six loadouts, real front112 result and front95 time roots, GameBattle.hud_input and Hud.queue_text. Compares seven native-oracle conditions per loadout including absent/stale VM, hidden show flag, invalid encoding and1000-second frame cap, all request bytes/position/color/font/pass/scale. Real ANM retirement and stale time show-flag reset observed. Reward/time inputs and VM alpha controlled; no artificial campaign-clear claim. Full draw finite submissions are checked, not native GPU/pixel/audio equality.',sourceHashes:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log(`PASS ${cases} actual GameSession awards/time layouts; ${submissions} submissions; six original time-VM retirement routes`);
