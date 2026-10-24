// Exact retail score helper control. Full pause scheduling is checked separately.
import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write,mkdirSync as mkdir}from'node:fs';
import{resolve,dirname}from'node:path';
import{createHash}from'node:crypto';
import{execFileSync}from'node:child_process';
import{WASI}from'node:wasi';
import{nativePython}from'./native-python.mjs';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
assert(process.argv[2],'Pass a current core build report with hashed objectBindings.');
const reportPath=resolve(process.argv[2]),build=JSON.parse(read(reportPath)),out=resolve(root,'artifacts/th14/paused-score-check');mkdir(out,{recursive:true});
for(const r of build.objectBindings)assert.equal(sha(read(r.path)),r.sha256,r.path);
for(const[name,digest]of Object.entries({...build.sourceHashes,...build.headerHashes})){
 assert.equal(sha(read(resolve(dirname(reportPath),'source',name))),digest,name+' frozen');
 if(!name.endsWith('/ResourceCrypt.cpp'))assert.equal(sha(read(resolve(root,'runtimes/th12',name))),digest,name+' workspace');
}
nativePython('tools/th14-paused-score-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='runtimes/th12/th12_web/tests/cpp/th14-paused-score-fixture.cpp',wasm=resolve(out,'unit.wasm');
execFileSync(resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',resolve(root,fixture),...build.objectBindings.map(r=>r.path),'-o',wasm],{cwd:root,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out}});
const bytes=read(wasm),proof=JSON.parse(read(resolve(out,'native.json'))),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const r of proof.cases){const actual=Array.from({length:5},(_,field)=>c.run(r.current,r.displayed,r.speed,r.high,r.continues,r.highContinues,r.flags,field)>>>0);assert.deepEqual(actual,r.result,JSON.stringify(r));}
const report={passed:true,cases:proof.cases.length,originalExecutableSha256:proof.originalExecutableSha256,originalEntry:proof.originalEntry,instructionBytesPatched:0,controlledHudAndGlobals:true,wasmSha256:sha(bytes),coreBuildReportSha256:sha(read(reportPath)),fixtureSha256:sha(read(resolve(root,fixture))),scope:'Unmodified retail434360 score callback: displayed score, speed, high score, high continues and flags.336 explicit current/display/speed/flag combinations include negative differences and paused/demo flags. This helper unit does not prove Scheduler registration, whole HUD, GPU or complete-game equivalence; full-process terminal HUD observations and production Replay-menu integration are separate controls.',completeGame:false,nativeEquivalent:false};
write(resolve(root,'docs/porting/th14-paused-score-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:report.cases}));
