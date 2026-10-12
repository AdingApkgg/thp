import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/spell-timeout-session-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-spell-timeout-session-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),path=resolve(out,'timeout-session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const table=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-menu-table-native.json'),'utf8'));
const cards=process.argv.includes('--all')?Array.from({length:120},(_,n)=>n):[0,26,119];
const loadouts=process.argv.includes('--six-loadouts')?[0,1,2,3,4,5]:[0];
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));},state=()=>Array.from({length:13},(_,n)=>c.timeout_state(n)>>>0);
const rows=[];let sampledFrames=0;
outer:for(const selection of loadouts)for(const id of cards){
 let stage=0;for(let n=0;n<7;++n)for(let r=0;r<table.rows[n];++r){const choices=table.table[n].slice(r*5,r*5+5);if(choices.slice(0,choices.findIndex(v=>v<0)).includes(id))stage=n+1;}
 const row={id,stage,selection,difficulty:table.difficulty[id],frames:0,activeAt:0,endAt:0,error:''};rows.push(row);
 try{
  assert.equal(c.spell_session_begin(stage,id,selection,row.difficulty),1,string(c.error()));
  let active=false;
  for(let frame=1;frame<=14000;++frame){
   assert.equal(c.combat_tick(0),1,string(c.error()));assert.equal(c.draw(),1,string(c.error()));
   const s=state();if(s[0]&1){if(!active){row.activeAt=frame;active=true;}}else if(active&&!row.endAt)row.endAt=frame;
   assert.equal(c.timeout_clock(frame/60),1,'post-draw clock');++sampledFrames;row.frames=frame;
   if(c.phase()!==1)break;
  }
  row.final=state();row.phase=c.phase();row.bulletSkippedMask=c.bullet_skipped_mask();row.bulletUnsupportedNativeMask=c.bullet_unsupported_native_mask();
  assert.ok(row.activeAt&&row.endAt,'actual ECL begins and ends the spell');assert.equal(row.phase,3,'actual ECL reaches result menu before cap');
  assert.equal(row.final[4],1,'clock writes once');assert.equal(row.final[8],row.final[3],'clock result equals stored time');assert.ok(row.final[2]>0);
  assert.equal(row.bulletSkippedMask,0);assert.equal(row.bulletUnsupportedNativeMask,0);
 }catch(e){row.error=e.message;row.final=state();row.phase=c.phase();row.diagnostic=string(c.progression_diagnostic());console.log(JSON.stringify(row));break outer;}
 console.log(JSON.stringify(row));
}
const sha=b=>createHash('sha256').update(b).digest('hex'),passed=rows.length===cards.length*loadouts.length&&rows.every(r=>!r.error);
const name=process.argv.includes('--all')?'th14-spell-timeout-all-session-observed-oct11.json':'th14-spell-timeout-session-observed-oct11.json';
writeFileSync(resolve(root,'docs/porting',name),JSON.stringify({passed,completeGame:false,nativeEquivalent:false,combatIsolation:true,forcedInvincibility:true,extraFirepower:false,artificialClear:false,sampledFrames,rows,wasmSha256:sha(bytes),archiveSha256:sha(archive),scope:'Actual original SpellPr ECL through timeout and result request, with no input/firepower/forced clear. Diagnostic combat_tick holds invulnerability each frame to reach later branches; not ordinary survival/capture or native combat equality. Real update/draw/post-draw clock and one recorded timing field checked; no native GPU/audio or browser timing comparison.',sources:Object.fromEntries([fixture,'tests/cpp/th14-startup-fixture.cpp','tests/cpp/th14-session-fixture.cpp','cpp/game/SpellController.cpp','cpp/game/GameSession.cpp','cpp/game/GameBattle.cpp','cpp/game/EnemyTh14Commands.cpp','cpp/game/HudTh14Notice.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');
if(!passed)process.exitCode=1;else console.log(`PASS ${rows.length} isolated actual ECL spell timeout routes / ${sampledFrames} update/draw/clock frames`);
