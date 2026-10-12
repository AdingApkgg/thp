// Executes the production stage entry directly; failures stay failures in the report.
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web');
const labelArg=process.argv.indexOf('--label'),label=labelArg<0?'':process.argv[labelArg+1];
if(label&&!/^[a-z0-9-]{1,64}$/.test(label))throw Error('invalid --label');
const out=resolve(root,'artifacts/th14/session-check',label);mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--reuse-build'))execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
// Capture this build before long sessions permit another build to replace metadata.
const engineBuild=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'),'utf8'));
if(process.argv.includes('--reuse-build')){
 for(const [path,expected] of Object.entries(engineBuild.sourceHashes))if(createHash('sha256').update(readFileSync(resolve(rt,path))).digest('hex')!==expected)throw Error('stale reused engine source: '+path);
 const enginePath=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14.wasm');
 if(createHash('sha256').update(readFileSync(enginePath)).digest('hex')!==engineBuild.sha256)throw Error('stale reused engine artifact');
}
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','tests/cpp/th14-session-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path);
const wasmBytes=readFileSync(wasm),sha=b=>createHash('sha256').update(b).digest('hex');
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
// Archive retains the source buffer; keep it alive throughout the session.
const p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);if(!c.open_archive(p,dat.length))throw Error('archive open');
const frameArg=process.argv.indexOf('--frames'),frameLimit=frameArg>=0?Number(process.argv[frameArg+1]):600;
if(!Number.isSafeInteger(frameLimit)||frameLimit<1||frameLimit>360000)throw Error('invalid --frames');
const stageArg=process.argv.indexOf('--stage'),singleStage=stageArg<0?1:Number(process.argv[stageArg+1]);
if(!Number.isSafeInteger(singleStage)||singleStage<1||singleStage>7)throw Error('invalid --stage');
const stages=process.argv.includes('--all')?[1,2,3,4,5,6,7]:[singleStage],rows=[];
const heldArg=process.argv.indexOf('--held'),held=heldArg<0?0:Number(process.argv[heldArg+1]);if(!Number.isSafeInteger(held)||held<0||held>0xffff)throw Error('invalid --held');
const combat=process.argv.includes('--combat'),tick=combat?c.combat_tick:c.tick;
const option=(name,fallback)=>{const at=process.argv.indexOf(name);const n=at<0?fallback:Number(process.argv[at+1]);if(!Number.isSafeInteger(n))throw Error('invalid '+name);return n;};
const character=option('--character',0),subtype=option('--subtype',0),difficulty=option('--difficulty',-1);
if(character<0||character>2||subtype<0||subtype>1||difficulty<-1||difficulty>4)throw Error('invalid TH14 selection');
if(difficulty===4&&(stages.length>1||singleStage!==7))throw Error('Extra difficulty requires stage 7');
if(stages.length===1&&singleStage===7&&difficulty>=0&&difficulty!==4)throw Error('stage 7 requires Extra difficulty');
const longRecording=process.argv.includes('--long-recording');if(longRecording&&!combat)throw Error('--long-recording requires --combat');c.allow_long_recording(longRecording?1:0);
for(const stage of stages){
 const selectedDifficulty=stage===7?4:difficulty<0?1:difficulty;
 console.log(JSON.stringify({event:'stage-start',stage,character,subtype,difficulty:selectedDifficulty}));
 let error='',errorStack='',frames=0,submissions=0;
 try{if(!c.begin(stage,character,subtype,selectedDifficulty))throw Error(string(c.error()));
  for(;frames<frameLimit;++frames){if(!tick(held)||!c.draw())throw Error(string(c.error()));submissions+=c.value(4);if(c.phase()!==1){++frames;break;}}
 }catch(e){error=e.message;errorStack=e.stack||'';}
 const total=c.creation_count(),recentAnimations=error?Array.from({length:Math.min(total,12)},(_,i)=>Array.from({length:6},(_,k)=>c.creation(total-Math.min(total,12)+i,k))):[];
 const laserRequest=error&&[702,703,711,713].includes(c.value(2))?Array.from({length:(c.value(2)===703?0x374:0x354)/4},(_,n)=>c.enemy_laser_request(n)>>>0):[];
 rows.push({stage,currentStage:c.value(1),stageFrame:c.value(0),frames,phase:c.phase(),phaseName:['title','stage','paused','game-over-or-results','finished','ending'][c.phase()],stageExit:c.stage_exit(),completedResult:c.completed_result(),submissions,error,errorStack,opcode:c.value(2),eclDiagnostic:error?string(c.ecl_diagnostic()):'',enemyError:string(c.enemy_error()),enemyDrop:error?Array.from({length:15},(_,n)=>c.enemy_drop(n)):[],laserRequest,laserDiagnostic:error?Array.from({length:5},(_,n)=>c.laser_diagnostic(n)):[],progressionDiagnostic:string(c.progression_diagnostic()),playerDiagnostic:Array.from({length:9},(_,n)=>c.player_diagnostic(n)),anmError:c.anm_error(),itemCollectType:c.item_collect_type(),bulletSkippedMask:c.bullet_skipped_mask()>>>0,bulletUnsupportedNativeMask:c.bullet_unsupported_native_mask()>>>0,unsupportedNativeBulletTransforms:Array.from({length:32},(_,bit)=>(2**bit)>>>0).filter(op=>(c.bullet_unsupported_native_mask()&op)!==0).map(op=>'0x'+op.toString(16)),recentAnimations,lastResource:string(c.last_file())});if(error)break;
}
const report={passed:rows.length===stages.length&&rows.every(r=>!r.error),combatIsolation:combat,scope:combat?'Original-resource stage scripts with player invulnerability held by the fixture; this isolates ECL progression and does not verify normal gameplay.':'Original-resource stage entry, update and command recording, stopping on phase changes; no native gameplay or GPU pixel equivalence claim.',rows};
report.held=held;report.requestedFrames=frameLimit;
report.character=character;report.subtype=subtype;report.difficulty=difficulty<0?'Normal / Extra by stage':difficulty;
report.extraDifficulty=stages.includes(7)?4:null;
report.longRecording=longRecording;report.discardedRecordingChunks=c.recording_chunk_count();if(longRecording)report.scope+=' Recorder-only chunks are discarded before the 86400-frame limit; this run does not verify replay recording or saving.';
report.sessionWasmSha256=sha(wasmBytes);report.archiveSha256=sha(dat);
report.engineBuild=engineBuild;
for(const r of rows)r.termination=r.error?'error':r.phase!==1?'phase-change':'frame-limit';
writeFileSync(resolve(out,held?(combat?'combat-shoot-result.json':'shoot-result.json'):(combat?'combat-result.json':'result.json')),JSON.stringify(report,null,2)+'\n');
const {engineBuild:buildMetadata,...summary}=report;console.log(JSON.stringify(summary));if(!report.passed)process.exitCode=1;
