import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/screen-fade-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-screen-fade-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out},wasm=resolve(out,'screen-fade.wasm'),fixture='tests/cpp/th14-screen-fade-fixture.cpp';
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/screen-fade-native.json'),'utf8'));let frames=0;
for(const row of proof.rows){c.initialize(row.kind,row.duration,row.rate);for(let n=0;n<row.states.length;n++){const s=row.states[n],label=`type ${row.kind} duration ${row.duration} rate ${row.rate} frame ${n}`;assert.equal(c.tick(s.stopped,s.frozen),s.result,label);assert.deepEqual([0,1,2,3].map(n=>c.value(n)>>>0),s.words,label);++frames;}}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,timelines:proof.rows.length,frames,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,'cpp/game/ScreenFade.cpp','cpp/game/ScreenFade.hpp','cpp/game/Timer.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-screen-fade-native.py','tools/th14-screen-fade-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))])),scope:'Full retail 46c400 (type0/3) and 46c970 (type2/5) alpha/lifetime/timer callbacks, 8 durations including negative/zero, six rates including near-one branches, stopped requests and controlled game-control freeze. Compares return, alpha, previous/current/fractional words. Local lifetime fixture ignores one stop request to continue probing. Rate pointer valid; native registration, GPU, geometry and remaining effect types excluded.'};
writeFileSync(resolve(root,'docs/porting/th14-screen-fade-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.timelines} fade timelines / ${frames} callback states`);
