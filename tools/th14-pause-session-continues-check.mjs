// Session integration over the separately measured retail4490c0 menu rules.
import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write,mkdirSync as mkdir}from'node:fs';
import{resolve,dirname}from'node:path';
import{createHash}from'node:crypto';
import{execFileSync}from'node:child_process';
import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex');
assert(process.argv[2],'Pass a hashed current core build report; an optional second report checks the old object control.');
const out=resolve(root,'artifacts/th14/pause-session-continues-check');mkdir(out,{recursive:true});
const fixture='runtimes/th12/th12_web/tests/cpp/th14-pause-session-continues-fixture.cpp';
const oraclePath=resolve(root,'artifacts/th14/pause-controls-native-oct11.json'),oracle=JSON.parse(read(oraclePath));
const cases=oracle.rows.filter(r=>r.state===1&&r.timer===10&&r.pressed===0);assert.equal(cases.length,4);
async function check(reportPath,label,current){
 reportPath=resolve(reportPath);const build=JSON.parse(read(reportPath));
 for(const row of build.objectBindings)assert.equal(sha(read(row.path)),row.sha256,row.path);
 for(const[name,digest]of Object.entries({...build.sourceHashes,...build.headerHashes})){
  assert.equal(sha(read(resolve(dirname(reportPath),'source',name))),digest,name+' frozen');
  if(current&&!name.endsWith('/ResourceCrypt.cpp'))assert.equal(sha(read(resolve(root,'runtimes/th12',name))),digest,name+' current');
 }
 const wasm=resolve(out,label+'.wasm');
 execFileSync(resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',resolve(root,fixture),...build.objectBindings.map(r=>r.path),'-o',wasm],{cwd:root,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out}});
 const bytes=read(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,rows=[];
 for(const row of cases){assert.equal(c.run(row.continues,row.replay),1);const actual={continues:c.value(0),state:c.value(1),cursor:[2,3,4,5].map(c.value),disabled:Array.from({length:c.value(5)},(_,i)=>c.disabled(i))},expected={continues:row.continues,state:row.nextState,cursor:row.cursor,disabled:row.disabled};rows.push({replay:row.replay,continues:row.continues,actual,expected,passed:JSON.stringify(actual)===JSON.stringify(expected)});}
 return{label,wasmSha256:sha(bytes),coreBuildReportSha256:sha(read(reportPath)),cases:rows,allPassed:rows.every(r=>r.passed)};
}
const current=await check(process.argv[2],'current',true),baseline=process.argv[3]?await check(process.argv[3],'before',false):null;
assert(current.allPassed);if(baseline)assert.equal(baseline.cases.filter(r=>!r.passed).length,2);
const report={passed:true,cases:4,current,baseline,originalExecutableSha256:oracle.executableSha256,originalMenuEntry:'4490c0',oracleSha256:sha(read(oraclePath)),fixtureSha256:sha(read(resolve(root,fixture))),sourceHashes:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/GameSession.cpp',fixture].map(n=>[n,sha(read(resolve(root,n)))])),scope:'Real GameSession::pause construction propagates the current battle HUD continue count into the separately measured retail4490c0 five-choice controller. Four original helper cases cover normal/replay with zero/one continue, including the duplicate disabled2 entry. Synthetic ANM scripts delimit graphics delivery; controlled counter values are explicit. This is a session-binding regression, not complete original ordinary gameplay or pixel/PCM equivalence.',completeGame:false,nativeEquivalent:false};
write(resolve(root,'docs/porting/th14-pause-session-continues-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:4,oldObjectFailures:baseline?.cases.filter(r=>!r.passed).length??null}));
