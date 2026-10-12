import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/screen-shake-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th16-screen-shake-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-screen-shake-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'shake.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/screen-shake-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.begin(r.duration,r.start,r.end,r.rate,r.seed),0,`command ${index}`);
 assert.deepEqual(Array.from({length:7},(_,n)=>c.initial(n)>>>0),r.initial,`constructor ${index}`);
 for(const [frame,row] of r.rows.entries()){c.tick(r.stopped);assert.deepEqual(Array.from({length:8},(_,n)=>c.value(n)>>>0),row,`frame ${index}/${frame}`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/ScreenShake.cpp','cpp/game/ScreenShake.hpp','cpp/game/Timer.hpp','cpp/game/Rng.hpp','cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp'];
const report={passed:true,cases:proof.cases.length,frames:proof.cases.reduce((n,r)=>n+r.rows.length,0),nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual ECL 517 dispatch 421681, factory 45d150, constructor 45d1a0 and 45cd30 update including actual shared RNG 402be0. Constructor arguments, timer, stop/removal result, signed amplitude wrap, SSE rounding, raw camera offsets and RNG state/call counts compared across seven durations/amplitude pairs, five rates, three seeds and stop states. Allocation and callback registration plus integer argument wrapper are controlled. Scaled render offsets, callback-list ordering across multiple effects, GPU pixels and complete gameplay remain unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th16-screen-shake-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail shake timelines, ${report.frames} frames.`);
