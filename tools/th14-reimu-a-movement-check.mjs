import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/reimu-a-movement-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-reimu-a-movement-native.py',{cwd:root,stdio:'inherit',windowsHide:true});execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-reimu-a-controller-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'movement.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/reimu-a-movement-native.json'),'utf8'));
for(const r of proof.rows){c.move(...r.args);assert.deepEqual([c.move_value(0)>>>0,c.move_value(1)>>>0],r.result,JSON.stringify(r.args));}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-reimu-a-movement-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Exact retail 44d621..44d67a SSE displacement calculation compared with the helper called by production PlayerMotion. Negative scale -128, truncation, wrapping subtraction, int-to-float rounding and factor product across signed directions, nonintegral shifts, factors 0/.2/.33/1/1.25 and i32 edge values. Keyboard direction selection, focus, touch input, bounds, body transitions and complete movement order are separate.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))]))},null,2)+'\n');console.log(`PASS: ${proof.rows.length} retail displacement calculations.`);
