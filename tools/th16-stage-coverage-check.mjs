import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/stage-coverage-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'coverage.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16','tests/cpp/th16-stage-coverage-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th16/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th16.dat'].path),bytes=readFileSync(wasm);
async function fresh(){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));},p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);if(!c.open_archive(p,dat.length))throw Error('archive');
 const trace=c.trace_address(),instruction=c.last_instruction_address(),argument=c.last_argument_address();
 const diagnose=(run,e)=>{const m=new DataView(c.memory.buffer);run.error=e.message;run.stack=e.stack;run.traceCode=m.getInt32(trace,true);const ip=m.getUint32(instruction,true);run.lastArgument=m.getInt32(argument,true);if(ip)run.lastInstruction={address:ip,bytes:Array.from(new Uint8Array(c.memory.buffer,ip,32))};if(!(e instanceof WebAssembly.RuntimeError)){run.frameFailure=Array.from({length:15},(_,n)=>c.frame_failure_word(n));run.spawnFailure=c.spawn_failure();run.failedSpawnName=string(c.failed_spawn_name());const failure=c.script_error_address();if(failure)run.failedInstruction=Array.from(new Uint8Array(c.memory.buffer,failure,32));run.lastOpcode=c.value(2);if(run.lastOpcode===702){run.laserRequests=Array.from({length:16},(_,index)=>({index,words:Array.from({length:0x358/4},(_,n)=>c.failed_laser_request_word(index,n)>>>0)}));}run.bulletDiagnostic=Array.from({length:22},(_,n)=>c.bullet_diagnostic(n));run.battleDiagnostic=Array.from({length:7},(_,n)=>c.battle_diagnostic(n));if(run.battleDiagnostic[1]===1699){run.damageSources=[];for(let id=1;id<=256;id++)if((c.damage_source_word(id,0)&1)&&c.damage_source_word(id,36)&&c.damage_source_word(id,35)){const words=Array.from({length:37},(_,n)=>c.damage_source_word(id,n)>>>0);run.damageSources.push({id,words,shot:Array.from({length:6},(_,n)=>c.source_shot_word(words[34],n)>>>0)});}}}};
 return {c,string,diagnose};
}
const selectedStage=Number(process.env.TH16_COVERAGE_STAGE||0),selectedDifficulty=process.env.TH16_COVERAGE_DIFFICULTY;
if(selectedStage&&!Number.isInteger(selectedStage)||selectedStage<0||selectedStage>7)throw Error('invalid selected stage');
const cases=[],sha=b=>createHash('sha256').update(b).digest('hex'),limit=Number(process.env.TH16_COVERAGE_FRAMES||6000);
if(!Number.isInteger(limit)||limit<1||limit>60000)throw Error('invalid frame limit');
for(let stage=selectedStage||1;stage<=(selectedStage||7);stage++)for(let difficulty=0;difficulty<(stage===7?1:4);difficulty++){
 if(selectedDifficulty!==undefined&&difficulty!==Number(selectedDifficulty))continue;
 const {c,string,diagnose}=await fresh();
 const run={kind:'controlled-stage',stage,difficulty:stage===7?4:difficulty,forcedInvincibility:true,frames:0,phase:1,error:''};cases.push(run);
 try{if(!c.begin_stage_season(stage,0,0,run.difficulty))throw Error(string(c.error()));run.resourceSlots=Array.from({length:4},(_,n)=>({name:string(c.resource_name(n)),valid:!!c.resource_slot_valid(n)}));if(run.resourceSlots.some(r=>!r.valid))throw Error('ANIM slot mapping');if(!c.upgrade(400,1140))throw Error('upgrade');for(;run.frames<limit;run.frames++){c.coverage_invincibility();if(!c.tick_input(9,0)||!c.draw())throw Error(string(c.error()));run.phase=c.phase();if(run.phase!==1){run.frames++;break;}}}catch(e){diagnose(run,e);}console.log(JSON.stringify(run));
}
for(let demo=0;demo<(selectedStage?0:4);demo++){
 const {c,string,diagnose}=await fresh();
 const run={kind:'original-demo',demo:demo+1,forcedInvincibility:false,frames:0,phase:1,error:''};cases.push(run);try{if(!c.begin_demo(demo))throw Error(string(c.error()));for(;run.frames<limit;run.frames++){if(!c.tick_input(0,0)||!c.draw())throw Error(string(c.error()));run.phase=c.phase();if(run.phase!==1){run.frames++;break;}}}catch(e){diagnose(run,e);}console.log(JSON.stringify(run));
}
writeFileSync(resolve(root,selectedStage?`docs/porting/th16-stage${selectedStage}-coverage-progress-oct10.json`:'docs/porting/th16-stage-coverage-progress-oct10.json'),JSON.stringify({title:16,completeGame:false,frameLimit:limit,cases,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Diagnostic only. Direct stage entries use forced invincibility and synthetic power/season energy to reveal later script gaps. Original demo cases use shipped replay data without forced invincibility. No native equivalence, natural stage progression or complete-game claim.'},null,2)+'\n');
console.log(`Coverage: ${cases.filter(r=>!r.error).length}/${cases.length} cases without a detected stop`);

