import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/laser-shell-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-laser-shell-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'shell.wasm'),fixture='tests/cpp/th14-laser-shell-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/laser-shell-native.json'),'utf8'));
const run=r=>{const p=c.allocate(0x354);try{new Uint32Array(c.memory.buffer,p,r.request.length).set(r.request);assert.equal(c.run(p,r.count??0,r.nextId??65536,r.rate)>>>0,r.result);}finally{c.release(p);}};
const snapshot=()=>Array.from({length:19},(_,n)=>c.value(n)>>>0);
for(const r of proof.cases){run(r);assert.deepEqual(snapshot(),r.snapshot,JSON.stringify(r));if(r.history.length){assert.deepEqual(Array.from({length:512},(_,n)=>c.history(n)>>>0),r.history);assert.deepEqual(Array.from({length:0x354/4},(_,n)=>c.copied(n)>>>0),r.copied);assert.equal(c.spatial_cancel(),0);}}
for(const r of proof.timelines){run(r);assert.deepEqual(snapshot(),r.frames[0]);for(let j=0;j<12;++j){if(j===6)assert.equal(c.cancel(r.reward,r.skip),0);assert.equal(c.tick(),0);assert.deepEqual(snapshot(),r.frames[j+1],`rate ${r.rate} reward ${r.reward} skip ${r.skip} variant ${r.variant} frame ${j}`);}}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,factoryCases:proof.cases.length,timelines:proof.timelines.length,frames:proof.timelines.reduce((n,r)=>n+r.frames.length,0),nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 43a750 kind 3 uses actual ctor 43a940 / initializer 443920 and vtable 4be364: update 443c50, draw 443c60 and collision/spatial cancel methods return zero in this executable. This is a registry object, not a visible curved laser. Compares capacity 256, issued-id wrap, request-overwritten object id, copied request, 512 history values, position/scalars, timer and native cancel flags through actual manager 43a570/43a670 and cancel 443cb0. Allocation/free/memset are controlled host-library boundaries. No claim for other laser kinds, GPU pixels or all lasers.',sourceHashes:Object.fromEntries([fixture,'cpp/game/LaserManager.cpp','cpp/game/LaserManager.hpp','cpp/game/LaserState.cpp','cpp/game/LaserState.hpp','cpp/game/EnemyTh14Commands.cpp','cpp/game/Timer.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-laser-shell-native.py','tools/th14-laser-shell-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-laser-shell-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.factoryCases} factory cases, ${report.timelines} registry/cancel timelines / ${report.frames} snapshots.`);
