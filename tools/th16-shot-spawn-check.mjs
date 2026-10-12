import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-spawn-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-spawn-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-spawn-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-spawn-native.json'),'utf8'));
let maxError=0;const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,number:r.number,kind:r.kind,angle:r.angle,speed:r.speed,focus:r.focus,family:r.family,seed:r.seed,rate:r.rate});assert.equal(c.begin(r.number,r.kind,r.angle,r.speed,r.focus,r.family,r.seed,r.rate),1,why);
 assert.deepEqual(Array.from({length:27},(_,k)=>c.value(k)>>>0),r.output,why);
 for(let k=0;k<8;k++){const actual=c.movement(k)>>>0,expected=r.movement[k];if(k<5||k===7)assert.equal(actual,expected,why+` field${k}`);else{const error=Math.abs(f(actual)-f(expected));maxError=Math.max(maxError,error);assert.ok(error<=0.00002,why+` field${k} error${error}`);}}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-spawn-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,resources:proof.resources,wasmSha256:sha(bytes),maxError,scope:'444e10 through4451ef before animation/damage allocation. Native visual RNG and402ff0 execute. State/timer/focus bits, both option families, beam cache, angle modes, random seed/calls exact; velocity tolerance2e-5 for x87 trig versus portable libm. Existing callbacks, allocation, delivery, subsequent motion/collision and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp','cpp/game/ShtResource.cpp','cpp/game/AnmManager.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-spawn-native.py','tools/th16-shot-spawn-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 shot spawn prefixes.`);
