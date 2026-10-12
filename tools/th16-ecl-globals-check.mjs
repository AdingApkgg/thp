import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/ecl-globals-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th16-ecl-globals-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-ecl-globals-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'globals.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/ecl-globals-native.json'),'utf8'));
for(const r of proof.cases){const data=Buffer.from(r.code,'hex'),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.run(p,r.present),0,JSON.stringify(r));assert.deepEqual(Array.from({length:39},(_,n)=>c.value(n)>>>0),r.storage,`storage ${r.id} ${r.present} ${r.value}`);assert.deepEqual([c.value(39)>>>0,c.value(40)>>>0],r.reads,`reads ${r.id} ${r.present} ${r.value}`);c.release(p);}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/EnemyState.cpp','cpp/game/EnemyState.hpp','cpp/game/EclContext.cpp','cpp/game/EclInterpreter.cpp','cpp/game/EnemyScript.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail VM 472030 runs push/store integer and float instructions 42..45 and subsequent integer/float global reads. Covers four manager integers -9926..-9923, eight manager floats -9922..-9915, four Boss integer and four Boss float destinations with Boss present/absent, and writable absolute/relative XY positions -9995..-9992. Native 423f80/424c10 writable-reference dispatch and 423810/424110 read dispatch execute without stubs; all 39 watched storage words and typed read results agree across 352 cases, including large signed integers, NaN/infinity and signed zero. Boss-missing writes fall back to owner storage while reads return zero. No claim about remaining globals, callbacks, complete gameplay or position recombination after writes.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};writeFileSync(resolve(root,'docs/porting/th16-ecl-globals-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail ECL global reference cases.`);
