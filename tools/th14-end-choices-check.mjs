import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/end-choices-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-end-choices-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-end-choices-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'end.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/end-choices-native.json'),'utf8'));
let inputCases=0;
for(const row of proof.rows){
 assert.equal(c.run(row.difficulty,row.continues,row.selected,row.pressed,row.repeat),1,JSON.stringify(row));
 const n=row.result;assert.equal(c.binding(),row.initial.scripts[0]);
 assert.deepEqual(Array.from({length:5},(_,i)=>c.value(i)),[n.selected,n.previous,n.count,n.wrap,n.disabled.length],JSON.stringify(row));
 assert.deepEqual(Array.from({length:c.value(4)},(_,i)=>c.disabled(i)),n.disabled,JSON.stringify(row));
 // Native state IDs 15/21 correspond to the older shared scheduler's 14/19.
 assert.equal(c.value(5),n.state===15?14:n.state===21?19:n.state,JSON.stringify(row));
 assert.deepEqual(Array.from({length:c.sound_count()},(_,i)=>c.sound(i)),n.sounds,JSON.stringify(row));
 if(row.selected>=0)inputCases++;
}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.rows.length,inputCases,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail TH14 main end-choice script, count, initial selection, disabled entries, cursor movement/repeat/cancel and Continue/Title/Retry confirmation sounds and scheduler transitions. Controlled ANM/audio boundaries; excludes helper manuals, ranking, replay I/O, child lookup/rendering and execution of exit destinations.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PauseEnd.cpp','cpp/game/PauseMenu.hpp','cpp/game/MenuCursor.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-end-choices-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} end-choice cases (${inputCases} input cases).`);
