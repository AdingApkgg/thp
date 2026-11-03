import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync as mkdir} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';

assert.equal(process.argv.length,4);assert.equal(process.argv[2],'--candidate');
const root=resolve(import.meta.dirname,'..'),candidate=resolve(root,process.argv[3]),home=resolve(candidate,'..');
const scope=relative(resolve(root,'artifacts/th14'),candidate);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const preparedBytes=read(resolve(candidate,'prepared.json')),prepared=JSON.parse(preparedBytes);
const baseBytes=read(resolve(root,prepared.baseBuild)),base=JSON.parse(baseBytes);assert.equal(sha(baseBytes),prepared.baseBuildSha256);
const unit=resolve(home,'unit');mkdir(unit);
const source=prepared.sourceRoot,oldSource=base.sourceSnapshotRoot;
const fixtureOriginal=resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-replay-rng-restore-fixture-nov04.cpp');
const fixture=resolve(unit,'fixture.cpp');write(fixture,read(fixtureOriginal));
const replay=resolve(source,'th12_web/cpp/game/Replay.cpp'),priorReplay=resolve(unit,'prior-replay.cpp');
const original=read(resolve(oldSource,'th12_web/cpp/game/Replay.cpp'));
assert.equal(sha(original),base.sourceHashes['th12_web/cpp/game/Replay.cpp']);
let text=original.toString().replaceAll('\r\n','\n');
const substitute=(old,value)=>{assert.equal(text.split(old).length-1,1,old);text=text.replace(old,value);};
substitute('#include "Rng.hpp"','#include "Rng.hpp"\n#include "ReplayRngRestoreTh14.hpp"');
substitute('    rng.seed=u16(seed);rng.calls=0;',`    rng.seed=u16(seed);
    ReplayRngRestoreScopeTh14::checkpoint(ReplayRngRestorePointTh14::GameplaySeedStored,rng,visual);
    rng.calls=0;
    ReplayRngRestoreScopeTh14::checkpoint(ReplayRngRestorePointTh14::GameplayCounterCleared,rng,visual);`);
substitute('    if(visual&&!first)visual->seed=u16(seed);',`    if(visual&&!first){visual->seed=u16(seed);
        ReplayRngRestoreScopeTh14::checkpoint(ReplayRngRestorePointTh14::ScriptSeedStored,rng,visual);}`);
write(priorReplay,text);
const originalSession=read(resolve(oldSource,'th12_web/cpp/game/GameSession.cpp'));
assert.equal(sha(originalSession),base.sourceHashes['th12_web/cpp/game/GameSession.cpp']);
assert.equal(originalSession.toString().split('recording_seed=rng.seed;rng.calls=0;animations.script_rng.seed=u16(recording_seed);').length-1,2);
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
assert.equal(sha(read(compiler)),base.compilerSha256);
const crypt=resolve(oldSource,'th12_web/cpp/game/ResourceCrypt.cpp');
assert.equal(sha(read(crypt)),'d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef');
const flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
 '-I'+resolve(source,'th12_web/cpp/game'),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576'];
const shared=[resolve(source,'th12_web/cpp/game/Lzss.cpp'),crypt];
const compile=(name,replayFile,extra)=>{
 const wasm=resolve(unit,name);execFileSync(compiler,[...flags,...extra,fixture,replayFile,...shared,'-o',wasm],
 {cwd:root,env:{...process.env,TEMP:unit,TMP:unit,TMPDIR:unit},stdio:'pipe',windowsHide:true});return wasm;
};
const candidateWasm=compile('candidate.wasm',replay,[]),priorWasm=compile('prior.wasm',priorReplay,['-DTH14_RESTORE_OLD_RECORD_ORDER=1']);
const instantiate=async(path)=>{
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const {instance}=await WebAssembly.instantiate(read(path),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);return instance.exports;
};
const c=await instantiate(candidateWasm),old=await instantiate(priorWasm);
const nativePath=resolve(home,'native-component.json'),nativeBytes=read(nativePath),native=JSON.parse(nativeBytes);
assert(native.executedOriginalReplayRecordStoresAndMainRng&&native.syntheticInputsAndCpuSchedule&&!native.liveOriginalProcess);
assert(native.instructionBytesUnmodified&&native.cases===15840&&native.profiles.length===native.cases);
assert.equal(native.toolSha256,sha(read(resolve(root,'tools/th14-replay-rng-restore-native-nov04.py'))));
const modeCounts=[0,0,0],priorFinalDifferences=[0,0,0],priorTraceDifferences=[0,0,0],firstPrior=[];
let traceSamples=0;
const get=(module,index)=>module.restore_value(index)>>>0;
for(const row of native.profiles){
 const mode=row.input[0];++modeCounts[mode];assert.equal(c.restore_probe(...row.input),1);
 assert.equal(old.restore_probe(...row.input),1);
 const actual=Array.from({length:9},(_,i)=>get(c,i)),prior=Array.from({length:9},(_,i)=>get(old,i));
 assert.deepEqual(actual,row.final,JSON.stringify(row.input));
 assert.equal(get(c,9),row.trace.length);
 const actualTrace=Array.from({length:get(c,9)},(_,i)=>Array.from({length:8},(_,j)=>get(c,10+i*8+j)));
 const oldTrace=Array.from({length:get(old,9)},(_,i)=>Array.from({length:8},(_,j)=>get(old,10+i*8+j)));
 assert.deepEqual(actualTrace,row.trace,JSON.stringify(row.input));
 if(JSON.stringify(prior)!==JSON.stringify(row.final)){
  ++priorFinalDifferences[mode];if(firstPrior.length<8)firstPrior.push({input:row.input,native:row.final,prior});
 }
 if(JSON.stringify(oldTrace)!==JSON.stringify(row.trace))++priorTraceDifferences[mode];
 traceSamples+=row.trace.length;
}
assert.deepEqual(modeCounts,[4320,5760,5760]);assert.equal(priorFinalDifferences[0],0);assert.equal(priorTraceDifferences[0],0);
assert(priorFinalDifferences[1]>0&&priorFinalDifferences[2]>0);
assert(priorTraceDifferences[1]>0&&priorTraceDifferences[2]>0);
const result={verifiedReplayAndRecordRngStoreOrder:true,cases:native.cases,modeCases:modeCounts,traceSamples,
 candidateFinalDifferences:0,candidateTraceDifferences:0,priorFinalDifferences,priorTraceDifferences,firstPrior,
 nativeProofSha256:sha(nativeBytes),nativeToolSha256:native.toolSha256,
 candidateWasmSha256:sha(read(candidateWasm)),priorWasmSha256:sha(read(priorWasm)),compilerSha256:sha(read(compiler)),
 preparedSha256:sha(preparedBytes),priorReplaySha256:sha(original),instrumentedPriorReplaySha256:sha(read(priorReplay)),
 originalSessionSha256:sha(originalSession),originalRecordFragmentsChecked:2,
 fixtureSha256:sha(read(fixtureOriginal)),headerSha256:sha(read(resolve(source,'th12_web/cpp/game/ReplayRngRestoreTh14.hpp'))),
 syntheticInputsAndCpuSchedule:true,optionalLockServicesDeclared:true,liveOriginalProcess:false,
 ordinaryWorkerSubstoreSchedulingImplemented:false,oldRngOrBulletFailuresClosed:false,
 rootGameplaySourcesModified:false,productionIntegrated:false,completeGame:false,nativeEquivalent:false,
 toolSha256:sha(read(import.meta.filename))};
write(resolve(home,'component-verified.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
