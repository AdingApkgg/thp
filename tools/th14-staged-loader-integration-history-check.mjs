// Restore the exact pre-cancellation private module and retain old API failures.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,readdirSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/staged-loader-integration-oct14'),oldRt=resolve(home,'revision-v1'),sha=b=>createHash('sha256').update(b).digest('hex');
const oldBuildBytes=readFileSync(resolve(oldRt,'private-build.json')),oldBuild=JSON.parse(oldBuildBytes),objects=resolve(oldRt,'objects');mkdirSync(objects,{recursive:true});
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14'];
for(const [p,h] of Object.entries(oldBuild.privateSourceHashes))assert.equal(sha(readFileSync(resolve(oldRt,p))),h,p);
const restoredObjects=[];
for(const source of oldBuild.sources){const name=source.replaceAll('/','_')+'.o',original=resolve(home,'objects',name),output=resolve(objects,name),key=relative(root,original).replaceAll('\\','/'),expected=oldBuild.objectHashes[key];
 if(sha(readFileSync(original))===expected)copyFileSync(original,output);
 else execFileSync(compiler,[...flags,'-I',resolve(home,'private/runtimes/th12/th12_web/cpp/game'),'-c',source,'-o',output],{cwd:oldRt,windowsHide:true,stdio:'inherit',env:{...process.env,TEMP:objects,TMP:objects,TMPDIR:objects}});
 assert.equal(sha(readFileSync(output)),expected,source);restoredObjects.push(output);
}
const fixture='tests/cpp/th14-staged-loader-integration-fixture.cpp';assert.equal(sha(readFileSync(resolve(oldRt,fixture))),oldBuild.fixtureSha256);
const oldWasm=resolve(oldRt,'staged-loader-integration-restored.wasm');
execFileSync(compiler,[...flags,'-I',resolve(home,'private/runtimes/th12/th12_web/cpp/game'),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...restoredObjects,'-o',oldWasm],{cwd:oldRt,windowsHide:true,stdio:'inherit',env:{...process.env,TEMP:objects,TMP:objects,TMPDIR:objects}});
assert.equal(sha(readFileSync(oldWasm)),oldBuild.wasmSha256,'Exact old private module restored');
const oldReplayReports=[];
for(const label of ['reimua-lunatic-controlled-v1','sakuyaa-normal-controlled-v1','reimub-lunatic-controlled-v1','reimua-extra-controlled-v1']){const path=resolve(home,'playback',label,'report.json'),bytes=readFileSync(path),report=JSON.parse(bytes);assert.equal(report.sourceBuildSha256,sha(oldBuildBytes));assert.equal(report.wasmSha256,oldBuild.wasmSha256);assert.equal(sha(readFileSync(resolve(home,'playback',label,'selected-state.u32'))),report.selectedStateSha256);assert.equal(sha(readFileSync(resolve(home,'playback',label,'callback-active.u8'))),report.callbackActiveSha256);oldReplayReports.push({label,reportSha256:sha(bytes),sourceBuildSha256:report.sourceBuildSha256,wasmSha256:report.wasmSha256});}
// Original baseline wrappers reject recording the same stage twice. This
// reproduces the failed unit input without invoking the new staged loader.
const duplicateHome=resolve(home,'baseline-duplicate-stage'),baseline=resolve(home,'baseline/runtimes/th12/th12_web');mkdirSync(duplicateHome,{recursive:true});
const duplicateSource=`#include "GameSession.hpp"\nusing namespace th11;\nstatic GameResources resources;static GameSession session;static u32 words[3]{};\nextern "C" __attribute__((export_name("allocate"))) u8* allocate(u32 n){return new u8[n];}\nextern "C" __attribute__((export_name("open"))) u32 open(const u8* p,u32 n){return resources.open_archive(p,n);}\nextern "C" __attribute__((export_name("duplicate"))) const u32* duplicate(){words[0]=session.begin(resources,1,0,0,1,false,false);words[1]=session.start_stage(resources,1);words[2]=session.error=="replay stage recording failed";return words;}\n`;
const duplicateFixture=resolve(duplicateHome,'fixture.cpp');writeFileSync(duplicateFixture,duplicateSource);
const shared=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),sharedFiles=readdirSync(shared).filter(n=>n.endsWith('.o')).sort().map(n=>resolve(shared,n)),sharedHashes=Object.fromEntries(sharedFiles.map(p=>[relative(root,p).replaceAll('\\','/'),sha(readFileSync(p))]));
for(const [p,h] of Object.entries(oldBuild.baselineSourceHashes))assert.equal(sha(readFileSync(resolve(root,'runtimes/th12/th12_web',p))),h);
const duplicateWasm=resolve(duplicateHome,'baseline.wasm');
execFileSync(compiler,[...flags,'-I',resolve(baseline,'cpp/game'),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',duplicateFixture,...sharedFiles,'-o',duplicateWasm],{cwd:duplicateHome,windowsHide:true,stdio:'inherit',env:{...process.env,TEMP:duplicateHome,TMP:duplicateHome,TMPDIR:duplicateHome}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(readFileSync(duplicateWasm),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open(p,archive.length),1);const q=c.duplicate(),duplicateWords=Array.from(new Uint32Array(c.memory.buffer,q,3));assert.deepEqual(duplicateWords,[1,0,1]);
for(const [p,h] of Object.entries(sharedHashes))assert.equal(sha(readFileSync(resolve(root,p))),h);
const result={historicalPrivateV1Restored:true,productionChanged:false,productionVerified:false,oldBuildSha256:sha(oldBuildBytes),oldWasmSha256:sha(readFileSync(oldWasm)),all141OldObjectHashesRestored:true,oldReplayReports,originalBaselineDuplicateStageWords:duplicateWords,baselineDuplicateFixtureSha256:sha(readFileSync(duplicateFixture)),baselineDuplicateWasmSha256:sha(readFileSync(duplicateWasm)),sharedObjectsReadOnly:true,sharedHashes,archiveSha256:sha(archive),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Old private v1 source/build/fixture and all141 object SHA are preserved; rebuilding only two changed objects reproduces the old WASM byte for byte. Four immutable v1 reports retain their own v1 module/build/state hashes. Original production wrappers independently reproduce the old same-recorded-stage Recorder rejection using read-only shared objects, without a staged-loader request. This preexisting invalid-input failure is retained, not skipped or renamed as a loader pass.'};
writeFileSync(resolve(home,'historical-v1-and-baseline-verified.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({historicalPrivateV1Restored:true,oldWasmSha256:result.oldWasmSha256,baselineDuplicateWords:duplicateWords}));
