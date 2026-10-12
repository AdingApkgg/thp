import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/demo-control-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-demo-control-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out},wasm=resolve(out,'demo-control.wasm');
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-demo-control-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const error=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const tick=(held=0,pause=0)=>assert.equal(c.control_tick(held,pause),1,error());
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/demo-control-native.json'),'utf8'));
let decisions=0;
for(const row of proof.rows){
 assert.deepEqual(row.fades,row.frame===3840?[[5,60,0,0,0,48]]:[]);
 if(row.system)continue;
 assert.equal(c.begin_interactive_demo(0),1,error());c.control_frame(row.frame);
 // Native bit 0x100 is pause; the front end's 0x100 is skip (native 0x80000).
 const held=(row.raw&~0x80100)|((row.raw&0x80000)?256:0),pause=!!(row.raw&256);
 tick(held,pause);assert.equal(c.phase(),1,'decision must preserve its combat callback');
 assert.equal(c.stage_frame(),row.frame+1);
 if(row.fades.length)assert.deepEqual([0,1,2,3].map(n=>c.demo_fade(n)),[5,60,0,48]);
 else assert.equal(c.demo_fade(0),-1);
 tick();assert.equal(c.phase(),row.transition?0:1,`frame ${row.frame} input ${row.raw.toString(16)}`);++decisions;
}
const runs=[];
for(let demo=0;demo<3;demo++){
 assert.equal(c.begin_interactive_demo(demo),1,error());let frames=0,fadeFrame=0;
 const selection=[0,1,2,3].map(n=>c.replay_observation(n));
 while(c.phase()===1&&frames<4000){
  tick();if(c.phase()!==1)break;++frames;
  if(c.demo_fade(0)===5&&!fadeFrame)fadeFrame=c.stage_frame();
  if(frames===3541||frames===3601)assert.equal(c.demo_fade(0),-1);
  if(frames===3901)assert.deepEqual([3,4,5].map(n=>c.demo_fade(n)),[48,61,255]);
  assert.equal(c.draw(),1,error());
  if(frames===3871)assert.equal(c.fade_draw_count(127,4),1,'priority 48 must submit once to the intermediate playfield target');
  if(frames===3901)assert.equal(c.fade_draw_count(255,4),1,'the final opaque fade must actually be drawn');
 }
 assert.equal(frames,3901);assert.equal(fadeFrame,3841);assert.equal(c.phase(),0);assert.equal(c.demo_flag(),0);
 assert.equal(c.bullet_skipped_mask(),0);assert.equal(c.bullet_unsupported_native_mask(),0);
 runs.push({demo,selection,combatFrames:frames,firstFadePlayerFrame:fadeFrame,returnedToTitle:true});
 console.log(`demo${demo}: ${frames} natural replay combat frames, fade at player frame ${fadeFrame}, title`);
}
// The other missing slot is the existing title fade at 61. A registered slot
// (67) must also draw once, without the old duplicate at SceneDrawKind::End.
c.title_fade();for(let n=0;n<31;n++)tick();assert.equal(c.draw(),1,error());assert.equal(c.fade_draw_count(127,0),1);
assert.equal(c.begin_interactive_demo(0),1,error());c.existing_priority_fade();for(let n=0;n<31;n++)tick();assert.equal(c.draw(),1,error());assert.equal(c.fade_draw_count(127,0),1);
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,nativeDecisions:proof.rows.length,productionDecisions:decisions,runs,fadeDrawing:{attractTarget:4,titleTarget:0,priorities:[48,61,67],eachDrawnOnce:true},nativeExecutableSha256:proof.executableSha256,archiveSha256:sha(dat),wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,'tests/cpp/th14-replay-session-fixture.cpp','tests/cpp/th14-session-fixture.cpp','cpp/game/GameSession.cpp','cpp/game/GameSession.hpp','cpp/game/GameBattle.cpp','cpp/game/ScreenFade.cpp','cpp/game/ScreenFade.hpp','cpp/game/SceneSchedule.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-demo-control-native.py','tools/th14-demo-control-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))])),scope:'Retail 436c08..436c7b attract input/timeout decisions; fade factory recorded. Local production decision clock selected separately, with remaining battle flags zero. Three unmodified original replays run interactively for 3901 combat callbacks, first fade at player frame 3841, priority 48, then title. Mid/final fade quad commands verified once on intermediate target; controlled priority 61/67 drawing checked once on screen. No invulnerability or power injection. Does not prove GPU fade pixels, title loading wall time, system-specific transition target or other titles.'};
writeFileSync(resolve(root,'docs/porting/th14-demo-control-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.nativeDecisions} native / ${decisions} production decisions, three interactive demos`);
