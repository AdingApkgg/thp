import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';

const root=resolve(import.meta.dirname,'..');
const [nativePath,outputPath,sourceRoot]=process.argv.slice(2);
assert.ok(nativePath&&outputPath,'Usage: node tool.mjs native-report.json new-output-directory');
const out=resolve(outputPath);
assert.ok(out.startsWith(resolve(root,'artifacts/th14')+'/')||out.startsWith(resolve(root,'artifacts/th14')+'\\'));
assert.ok(!existsSync(out));mkdirSync(out,{recursive:true});
const native=JSON.parse(readFileSync(nativePath));
assert.ok(native.passed&&native.countdownCases.length===9);
const game=resolve(root,sourceRoot??'runtimes/th12/th12_web');
const productionSource=resolve(game,'cpp/game/EnemyPhase.cpp');
const fixtureSource=resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-enemy-phase-fixture.cpp');
let fixture=fixtureSource;
if(sourceRoot){
 fixture=resolve(out,'fixture.cpp');
 const original=readFileSync(fixtureSource,'utf8');
 assert.equal(original.split('"../../cpp/game/EnemyState.hpp"').length,2);
 writeFileSync(fixture,original.replace('"../../cpp/game/EnemyState.hpp"',JSON.stringify(resolve(game,'cpp/game/EnemyState.hpp').replaceAll('\\','/'))));
}
const sources=[productionSource,fixture];
const headers=['cpp/game/EnemyState.hpp','cpp/game/HudScalarTh14.hpp','cpp/game/Timer.hpp'];
const wasm=resolve(out,'countdown.wasm');
execFileSync(resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),
 ['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
  '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:game,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},windowsHide:true,stdio:'pipe'});
const bytes=readFileSync(wasm);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
const rows=[];
for(const item of native.countdownCases){
 const p=c.allocate(item.inputs.length*4);
 try{
  new Uint32Array(c.memory.buffer,p,item.inputs.length).set(item.inputs);c.run(p);
  const actual=Array.from({length:23},(_,i)=>c.value(i)>>>0);
  assert.deepEqual(actual,item.result,`remaining ${item.remaining}`);
  rows.push({remaining:item.remaining,seconds:actual[10],hundredths:actual[11]});
 }finally{c.release(p);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const q={passed:true,cases:rows.length,rows,wasmSha256:sha(bytes),nativeReportSha256:sha(readFileSync(nativePath)),
 sourceHashes:Object.fromEntries([...sources,...headers.map(p=>resolve(game,p))].map(p=>[p,sha(readFileSync(p))])),
 fixtureOriginalSha256:sha(readFileSync(fixtureSource)),sourceRoot:game,
 toolSha256:sha(readFileSync(import.meta.filename)),actualProductionCountdownCompiled:true,
 originalEndMarkerDispatchCases:native.cases,fullOriginalEnemyCallbackExecuted:false,
 actualScreenshotCountdownStateAccepted:false,gameLogicChanged:false,completeGame:false};
writeFileSync(resolve(out,'report.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify(q));
