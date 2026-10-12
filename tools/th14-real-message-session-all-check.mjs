import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/dialogue-text-check'),sha=b=>createHash('sha256').update(b).digest('hex');
const objectPath=resolve(out,'objects.json'),objects=JSON.parse(readFileSync(objectPath));
for(const [p,h] of Object.entries(objects.objectHashes))assert.equal(sha(readFileSync(p)),h,p);
for(const [p,h] of Object.entries(objects.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,'stale source '+p);
const fixture='tests/cpp/th14-real-message-session-fixture.cpp',fixtureHash=sha(readFileSync(resolve(rt,fixture))),toolHash=sha(readFileSync(import.meta.filename)),wasm=resolve(out,'real-message-session-all.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory',fixture,...Object.keys(objects.objectHashes),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));},words=(p,n)=>Array.from(new Uint32Array(c.memory.buffer,p,n));
const matrixPath=resolve(root,'artifacts/th14/dialogue-real-message-matrix-native.json'),matrix=JSON.parse(readFileSync(matrixPath)),jobs=matrix.jobs;let frames=0,writes=0;const routes=[];
for(const job of jobs){console.log('Session original MSG group',job.stage,job.selection);const nativeBytes=readFileSync(resolve(root,job.path));assert.equal(sha(nativeBytes),job.sha256);const native=JSON.parse(nativeBytes);
 for(const r of native.rows){const [stage,selection,entry]=r.input;let comparedFrames=0;assert.equal(c.begin_session_message(stage,selection,entry,r.frames.length),1,JSON.stringify(r.input)+' '+text(c.error()));
  for(const [frame,f] of r.frames.entries()){const label=JSON.stringify({input:r.input,frame});assert.equal(c.step_session_message(),f.status,label+' '+text(c.error()));if(!f.status)assert.deepEqual(words(c.message_state(),20),f.dialogue.slice(0,20),label+' dialogue');
   const expected=f.writes.flatMap(w=>{const b=Buffer.from(w.text,'hex');return [w.line,w.color,w.font>>>0,w.offset>>>0,w.spacing>>>0,w.plain,b.length,...b];});assert.deepEqual(words(c.message_writes(),c.message_write_words()),expected,label+' queued text');++frames;++comparedFrames;writes+=f.writes.length;
   // This single-stage recording has no next-stage stream. Actual session
   // completion ends playback; the isolated native owner oracle continues
   // because its stage-complete service was intentionally controlled.
   if(c.session_phase()!==1){assert(f.effects.includes(3),label+' world exit without native stage-complete request');break;}
  }
  routes.push({input:r.input,comparedFrames,nativeFrames:r.frames.length,endedAtWorldExit:comparedFrames<r.frames.length,finalSessionPhase:c.session_phase(),finalBattleFrame:c.session_stage_frame(),nativeSha256:job.sha256});
 }
}
assert.equal(sha(readFileSync(resolve(rt,fixture))),fixtureHash);assert.equal(sha(readFileSync(import.meta.filename)),toolHash);
const report={passed:true,completeGame:false,nativeEquivalent:false,routes:routes.length,frames,writes,rows:routes,archiveSha256:sha(archive),nativeMatrixSha256:sha(readFileSync(matrixPath)),objectManifestSha256:sha(readFileSync(objectPath)),sourceHashes:objects.sourceHashes,wasmSha256:sha(bytes),fixtureSha256:fixtureHash,recordingGraphicsSha256:sha(readFileSync(resolve(rt,'tests/cpp/render-fixture.hpp'))),toolSha256:toolHash,scope:'Actual original DAT via GameResources, actual GameSession.begin/save/decode replay/update/draw, actual GameBattle and stage ECL/managers drive original MSG. Manually starts each chosen MSG entry after stage initialization. Controlled single-stage replay retains the original oracle edge stream (held0, pressed0x80001 every60 frames); not natural recorded player input. Compares20 live dialogue state/clock/cursor/background fields and every queued text request through owner end or actual session world exit; requires original stage-complete request on any earlier world exit. Original isolated owner oracle controls stage-complete service and continues after that boundary, so later frames are not compared here. No FontDevice/world-state/natural MSG trigger/survival/clear/graphics pixels/sound equivalence claim.'};
writeFileSync(resolve(root,'docs/porting/th14-real-message-session-all-verified-oct12.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,routes:routes.length,frames,writes}));
