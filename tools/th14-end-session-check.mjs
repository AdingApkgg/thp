import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/end-session-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-end-session-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'end-session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,sha=b=>createHash('sha256').update(b).digest('hex');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const error=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};let frames=0;
const tick=(held=0)=>{assert.equal(c.tick(held),1,error());assert.equal(c.draw(),1,error());++frames;};const wait=n=>{for(let i=0;i<n;i++)tick();};const press=k=>{tick(k);tick();};
let scoreNameEntries=0;
const reachChoices=()=>{
 for(let i=0;i<60&&c.value(1)!==14&&c.value(1)!==18;i++)tick();
 if(c.value(1)===18){
  // Native TH14 defaults rank10000, so this natural run now reaches ranking.
  // Finish the actual name-entry menu with keyboard input before Continue.
  wait(12);assert.ok(c.value(3)>=0&&c.value(3)<10);assert.equal(c.value(40),0);
  press(16);assert.equal(c.value(40),78);press(64);assert.equal(c.value(40),90);press(1);
  ++scoreNameEntries;
 }
 assert.equal(c.value(1),14);
};
const enter=()=>{assert.equal(c.begin(),1,error());for(let i=0;i<60&&c.value(1)!==14;i++)tick();assert.equal(c.value(0),3);assert.equal(c.value(1),14);assert.equal(c.value(2),5);assert.equal(c.value(10),139);assert.equal(c.value(11),34);};
const select=n=>{assert.equal(c.value(3),0);for(let i=0;i<n;i++)press(32);assert.equal(c.value(3),n);};const rows=[];
enter();select(1);press(1);wait(20);assert.equal(c.value(0),0);rows.push({action:'Title',passed:true});
enter();select(4);press(1);wait(20);assert.equal(c.value(0),1);rows.push({action:'Retry',passed:true});
enter();select(3);press(1);wait(45);assert.equal(c.value(6),1);assert.equal(c.value(4),1);assert.equal(c.value(5),0);
press(1);wait(25);assert.equal(c.value(4),4);assert.equal(c.value(7),1);const pageHashes=[c.value(9)>>>0];
for(let page=1;page<7;page++){press(32);wait(45);assert.equal(c.value(4),4);assert.equal(c.value(5),page);assert.equal(c.value(7),page+1);pageHashes.push(c.value(9)>>>0);}
press(16);wait(45);assert.equal(c.value(5),5);assert.equal(c.value(7),8);assert.equal(c.value(9)>>>0,pageHashes[5]);
press(2);wait(25);assert.equal(c.value(4),1);press(2);wait(35);assert.equal(c.value(6),0);assert.equal(c.value(1),14);assert.equal(c.value(3),3);assert.equal(c.value(8),1);rows.push({action:'Manual',passed:true,pages:7,pageLoads:8,pageHashes,returnedToEndMenu:true,releasedResources:true});
press(2);assert.equal(c.value(3),1);press(1);wait(20);assert.equal(c.value(0),0);
// First loss is produced by the real battle. Further losses control only the
// death boundary so the fixture reaches the entire Normal Continue budget.
assert.equal(c.begin_natural(),1,error());wait(120);
assert.deepEqual([33,34,35].map(n=>c.value(n)),[16,16,255],'sixteen sidebar icons must be registered on layer 24 and finish their native fade');
for(let i=0;i<4000&&c.value(0)===1;i++)tick();assert.equal(c.value(0),3);assert.equal(c.value(26),2);
const firstLossFrame=c.value(12),continueRows=[];
for(let count=1;count<=3;count++){
 reachChoices();assert.equal(c.value(3),0);assert.equal(c.value(2),5);
 const ids=[12,13,21,22,23,24,25,28,29,32],frozen=ids.map(n=>c.value(n));assert.ok(c.value(25)>0,'active bullet preservation must be exercised');
 press(1);for(let i=0;i<20&&c.value(0)===3;i++)tick();assert.equal(c.value(0),1);assert.deepEqual(ids.map(n=>c.value(n)),frozen,'Continue must preserve frame, stage, player/battle identity, enemies, bullets and recording clocks');
 assert.deepEqual([14,15,16,17,18,19,20,26,30,31].map(n=>c.value(n)),[2,0,2,0,400,0,count,2,4,0]);
 tick();assert.equal(c.value(26),0,'the preserved death lifecycle enters respawn on its next tick');assert.deepEqual([16,17].map(n=>c.value(n)),[3,0],'native respawn refills Bombs after Continue');wait(60);assert.equal(c.value(26),1);assert.equal(c.value(12),frozen[0]+61);
 continueRows.push({count,stage:frozen[1],lossFrame:frozen[0],bullets:frozen[6],preservedManagersAndClocks:true,respawned:true});
 for(let i=0;i<3000&&c.value(25)===0&&c.value(0)===1;i++)tick();assert.equal(c.value(0),1);assert.ok(c.value(25)>0,'wait for real bullets after the respawn cancel');c.force_loss();tick();
}
reachChoices();assert.equal(c.value(3),1,'Normal budget exhausted selects Title');press(16);assert.equal(c.value(3),4,'up skips disabled Continue/Save Replay');rows.push({action:'Continue',passed:true,firstLossFrame,naturalFirstLoss:true,rows:continueRows,limitEnforced:true,scoreNameEntries});
const report={passed:true,frames,rows,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Production session/menu/ANM/render commands with retail archive: Title/Retry, seven-page manual round trip and three in-place Normal Continues and keyboard-driven score name entry. First loss is natural, later loss boundaries controlled. Preserves stage/frame/battle/player/enemy/bullet identity and recording clocks and verifies stock reset, four options and port respawn. PNG delivery at effects boundary; excludes native death lifecycle equivalence, audio, replay saving and GPU pixels.',sourceHashes:Object.fromEntries([fixture,'cpp/game/GameSession.cpp','cpp/game/GameSession.hpp','cpp/game/ContinueTh14.cpp','cpp/game/ContinueTh14.hpp','cpp/game/GameEconomy.hpp','cpp/game/PlayerFrame.cpp','cpp/game/PlayerFrame.hpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp','cpp/game/Hud.cpp','cpp/game/HudTh14Text.cpp','cpp/game/HudTh14Text.hpp','cpp/game/Th14LifeFragments.hpp','cpp/game/ItemRewards.cpp','cpp/game/PauseEnd.cpp','cpp/game/PauseMenu.hpp','cpp/game/ScoreFile.cpp','cpp/game/ScoreFile.hpp','cpp/game/GameSessionResources.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};writeFileSync(resolve(root,'docs/porting/th14-end-session-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: Title, Retry, seven manual pages and three in-place Continues, ${frames} original-resource frames.`);
