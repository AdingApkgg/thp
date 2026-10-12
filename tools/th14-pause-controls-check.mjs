import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),label=process.argv[2]||'after';assert(/^[a-z0-9-]+$/.test(label));
const out=resolve(root,'artifacts/th14/pause-controls',label);mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs'),'--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-pause-controls-fixture.cpp',wasmPath=resolve(out,'pause.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasmPath],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasmPath),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const oraclePath=resolve(root,'artifacts/th14/pause-controls-native-oct11.json'),oracle=JSON.parse(readFileSync(oraclePath)),scripts=[118,119,120,127,128,151,78,79,80,87,88,152],cases=[];
for(const row of oracle.rows){assert.equal(c.run(row.state,row.timer,row.selected,row.pressed,row.replay,row.continues),1);const actual={state:c.value(0),cursor:[1,2,3,4].map(c.value),disabled:Array.from({length:c.value(4)},(_,n)=>c.disabled(n)),sounds:Array.from({length:c.value(7)},(_,n)=>c.sound(n)),children:scripts.map((_,n)=>c.child(n)),root:c.value(5)};
 const expected={state:row.nextState,cursor:row.cursor,disabled:row.disabled,sounds:row.sounds,children:scripts.map(()=>0),root:0};for(const [id,label] of row.events){if(id===100){expected.root=label;expected.children.fill(label);}else if(id>=1000){const n=scripts.indexOf(id-1000);assert(n>=0);expected.children[n]=label;}}
 cases.push({input:row,actual,expected,passed:JSON.stringify(actual)===JSON.stringify(expected)});
}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:cases.every(r=>r.passed),completeGame:false,nativeEquivalent:false,cases,nativeExecutableSha256:oracle.executableSha256,oracleSha256:sha(readFileSync(oraclePath)),wasmPath,wasmSha256:sha(bytes),engineBuild:JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'))),sourceHashes:Object.fromEntries([fixture,'cpp/game/PauseMenu.cpp','cpp/game/PauseReplay.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),scope:'Retail4490c0 pause-control native oracle: five-choice cursor/disabled entries, normal/replay selection, confirm/move/cancel states, child-script interrupt recipients and sound IDs. Synthetic ANM child trees delimit delivery; not GPU/frame animation or whole-game equivalence.'};
writeFileSync(resolve(out,'result.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,cases:cases.length,failures:cases.filter(r=>!r.passed).map(r=>({state:r.input.state,selected:r.input.selected,pressed:r.input.pressed,actual:r.actual,expected:r.expected}))}));if(!report.passed)process.exitCode=1;
if(report.passed&&label==='after')writeFileSync(resolve(root,'docs/porting/th14-pause-controls-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');
