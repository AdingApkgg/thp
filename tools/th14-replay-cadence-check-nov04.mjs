import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const out=resolve(root,'artifacts/th14/replay-cadence-nov04');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
execFileSync('C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',
 [resolve(root,'tools/th14-replay-cadence-native-nov04.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-replay-cadence-fixture.cpp',header='cpp/game/ReplayCadenceTh14.hpp',wasm=resolve(out,'cadence.wasm');
// Preserve the user's unrelated ResourceCrypt.cpp edit. This unit links the
// already verified crypt source from the frozen production build snapshot.
const base=JSON.parse(readFileSync(resolve(root,'artifacts/th14/frame-rng-scope-nov02/counter-production-core/observer-build.json')));
const crypt=resolve(base.sourceSnapshotRoot,'th12_web/cpp/game/ResourceCrypt.cpp');
assert.equal(sha(readFileSync(crypt)),base.sourceHashes['th12_web/cpp/game/ResourceCrypt.cpp']);
const sources=[fixture,'cpp/game/Replay.cpp','cpp/game/ReplayRecorder.cpp','cpp/game/Lzss.cpp'];
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),
 ['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',...sources,crypt,'-o',wasm],
 {cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const native=JSON.parse(readFileSync(resolve(out,'native.json')));assert(native.passed);
for(const row of native.cases)assert.equal(instance.exports.repeat(...row.slice(0,5)),row[5],JSON.stringify(row));
for(const row of native.dispatch){let frame=row.start,updates=0,again;
 do{frame=(frame+1)>>>0;++updates;again=instance.exports.repeat(row.controller,row.mode,row.flags,row.held,frame)===6;assert(updates<=8);}while(again);
 assert.equal(updates,row.updates);assert.equal(frame,row.final);
}
const c=instance.exports;let counterAssertions=0;
const eq=(a,b)=>{assert.equal(a,b);++counterAssertions;};
eq(c.start(),1);eq(c.callback_frame(),native.playbackInitialCallbackFrame);
eq(c.select_stage(1),1);eq(c.tick(0),0);eq(c.frame(),0);eq(c.callback_frame(),0);
eq(c.tick(1),0);eq(c.callback_frame(),1);eq(c.tick(1),0);eq(c.callback_frame(),2);
eq(c.tick(1),0);eq(c.frame(),3);eq(c.callback_frame(),3); // exhausted stream still advances
eq(c.select_stage(2),1);eq(c.frame(),0);eq(c.callback_frame(),3); // stage-local cursor resets
eq(c.tick(1),0);eq(c.callback_frame(),4);
eq(c.tick(1),1);eq(c.frame(),1);eq(c.callback_frame(),4);
eq(c.tick(1),1);eq(c.callback_frame(),4); // terminal marker is retained
eq(c.reopen(),1);eq(c.callback_frame(),0);
const report={passed:true,completeGame:false,nativeEquivalent:false,gateCases:native.cases.length,
 dispatcherCases:native.dispatch.length,counterAssertions,nativeExecutableSha256:native.nativeExecutableSha256,
 priorAlwaysSingleUpdateGateMismatches:native.cases.filter(row=>row[5]!==1).length,
 nativeProofSha256:sha(readFileSync(resolve(out,'native.json'))),wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,header,'cpp/game/Replay.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 frozenResourceCryptSha256:sha(readFileSync(crypt)),
 nativeToolSha256:sha(readFileSync(resolve(root,'tools/th14-replay-cadence-native-nov04.py'))),
 toolSha256:sha(readFileSync(import.meta.filename)),scope:native.scope};
writeFileSync(resolve(out,'verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,gateCases:report.gateCases,dispatcherCases:report.dispatcherCases,counterAssertions}));
