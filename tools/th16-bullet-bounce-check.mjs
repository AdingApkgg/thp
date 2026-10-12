import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/bullet-bounce-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-bullet-bounce-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'bounce.wasm'),fixture='tests/cpp/th16-bullet-bounce-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/bullet-bounce-native.json'),'utf8')),decode=b=>new Float32Array(new Uint32Array([b]).buffer)[0],floats=new Set([0,1,2,3,4,5,6,7,14,17,18,19,20]);let maxError=0,frames=0;
function compare(r,label){for(let n=0;n<25;n++){const actual=c.value(n)>>>0;if(floats.has(n)){const e=Math.abs(decode(actual)-decode(r.output[n]));maxError=Math.max(e,maxError);assert.ok(e<=.00004,`${label} field${n}: ${decode(actual)} != ${decode(r.output[n])}`);}else assert.equal(actual,r.output[n],`${label} field${n}`);}assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>[c.event(n,0)>>>0,c.event(n,1)>>>0]),r.events,label);}
// Retail413860 is void; its EAX residue is not a success/failure result.
for(const [n,r] of proof.cases.entries()){assert.equal(c.begin_case(...r.input),0,`case${n} init`);compare(r.initial,`case${n} init`);for(const [f,row] of r.timeline.entries()){assert.equal(c.step()>>>0,row.result,`case${n} frame${f}`);compare(row,`case${n} frame${f}`);frames++;}}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-bullet-bounce-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,initializers:proof.cases.length,frames,maximumObservedFloatError:maxError,nativeExecutableSha256:proof.executableSha256,scope:'Own413cb5 ETEX64 initialization and full411e70 timelines executing415bb0 and all four wall consumers.64 masks including count-only/custom bounds, strict/inclusive edges,0/negative/positive manager bounds, speed sentinel threshold, ordered corner reflections, completion and same-frame32768 continuation, concurrent ETEX1, rates and sounds. Collision/ANM/audio/retirement controlled; manager bounds supplied directly. ECL803 bounds setter, other transforms and full game excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/BulletTh16.cpp','cpp/game/BulletTh16.hpp','cpp/game/BulletManager.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} TH16 bounce initializers / ${frames} full frames; max error ${maxError}`);
