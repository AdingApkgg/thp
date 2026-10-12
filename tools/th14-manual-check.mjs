import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/manual-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-manual-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-manual-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'manual.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/manual-native.json'),'utf8'));
for(const row of proof.rows){
 assert.equal(c.run(row.phase,row.substate,row.timer,row.selected,row.pressed,row.repeat,row.origin),1,JSON.stringify(row));
 assert.deepEqual(Array.from({length:6},(_,i)=>c.value(i)),row.result,JSON.stringify(row));
 assert.deepEqual(Array.from({length:c.binding_count()},(_,i)=>c.binding(i)),row.scripts,JSON.stringify(row));
 assert.deepEqual(Array.from({length:c.binding_count()},(_,i)=>Array.from({length:3},(_,n)=>c.position(i,n)>>>0)),row.positions,JSON.stringify(row));
 assert.deepEqual(Array.from({length:c.sound_count()},(_,i)=>c.sound(i)),row.sounds,JSON.stringify(row));
 assert.deepEqual(Array.from({length:10},(_,i)=>c.label(i)),row.labels,JSON.stringify(row));
}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail TH14 help manager states, frame delays, seven categories/pages, wrap/repeat input, page requests, script bindings, interrupts and sounds. Controlled resource/PNG/ANM/audio boundaries; excludes threading, factory/GPU pixel output and PNG resampling.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PauseEnd.cpp','cpp/game/PauseMenu.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};writeFileSync(resolve(root,'docs/porting/th14-manual-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} native manual cases.`);
