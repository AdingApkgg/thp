// Real original replay inputs; this test does not force invulnerability or power.
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/replay-session-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const engineBuild=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'),'utf8'));
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'replay-session.wasm'),fixture='tests/cpp/th14-replay-session-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),bytes=readFileSync(wasm),cases=[];
for(let demo=0;demo<3;demo++){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));},p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);
 const observe=()=>Array.from({length:19},(_,n)=>c.replay_observation(n));
 const run={demo:`demo${demo}.rpy`,forcedInvincibility:false,syntheticPower:false,frames:0,error:''};cases.push(run);
 try{
  if(!c.open_archive(p,dat.length)||!c.begin_demo(demo))throw Error(string(c.error()));run.initial=observe();
  run.selectionMatches=run.initial.slice(0,3).every((v,n)=>v===run.initial[n+7]);
  run.recordedFrames=run.initial[4];run.checkpoints=[];
  for(;run.frames<60000;run.frames++){
   if(!c.tick(0)||!c.draw())throw Error(string(c.error()));
   if(run.frames%600===0)run.checkpoints.push({frame:run.frames+1,observation:observe()});
   if(c.phase()!==1){run.frames++;break;}
  }
  run.phase=c.phase();run.stageExit=c.stage_exit();run.final=observe();run.recordingFullyConsumed=run.final[5]>=run.recordedFrames;run.bulletSkippedMask=c.bullet_skipped_mask()>>>0;run.bulletUnsupportedNativeMask=c.bullet_unsupported_native_mask()>>>0;
 }catch(e){run.error=e.message;run.stack=e.stack;run.opcode=c.value(2);run.playerDiagnostic=Array.from({length:9},(_,n)=>c.player_diagnostic(n));run.laserDiagnostic=Array.from({length:5},(_,n)=>c.laser_diagnostic(n));}
 console.log(JSON.stringify(run));
}
const sha=b=>createHash('sha256').update(b).digest('hex'),passed=cases.every(r=>!r.error&&r.selectionMatches&&r.recordingFullyConsumed&&r.phase!==1&&!r.bulletSkippedMask&&!r.bulletUnsupportedNativeMask);
writeFileSync(resolve(root,'docs/porting/th14-original-replay-progress-oct10.json'),JSON.stringify({passed,completeGame:false,nativeEquivalent:false,cases,archiveSha256:sha(dat),wasmSha256:sha(bytes),engineBuild,scope:'Production session uses all three original TH14 attract replay files, actual recorded held/pressed/released bits and ordinary collision. No forced invulnerability, synthetic power, native frame-state equality, recorder/save proof or GPU pixel equivalence. Reports decoded selection against actual session selection and observed termination; early deaths can still represent desynchronization.'},null,2)+'\n');
console.log(`Original replay integration: ${cases.filter(r=>!r.error&&r.selectionMatches).length}/3 correct selections without runtime error; ${cases.filter(r=>r.recordingFullyConsumed).length}/3 full recorded streams consumed`);if(!passed)process.exitCode=1;
