import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-homing-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-homing-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-homing-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'homing.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-homing-native.json'),'utf8'));let maxError=0;
const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,...r});c.begin(r.state,r.target,r.age,r.speed,r.angle,...r.point,r.mode,r.flags);
 assert.equal(c.value(0)>>>0,r.output[0],why);assert.equal(c.value(1)>>>0,r.output[1],why);
 const error=Math.abs(f(c.value(2)>>>0)-f(r.output[2]));maxError=Math.max(maxError,error);assert.ok(error<=.000002,why+` angle error${error}`);
 assert.deepEqual(Array.from({length:c.count()},(_,n)=>[c.event(n,0)>>>0,c.event(n,1)>>>0]),r.events,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-homing-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Full445ee0, native atan2 and4052e0/411410 execute. Nearest request256 at unshifted shot position, absent/stale/protected IDs, retained protected ID, state2,60-frame boundary, speed thresholds and limits, wrapped angle and steering .08. Enemy nearest/valid/lookup controlled boundaries. Exact speed/id and request sequence, atan2 angle tolerance2e-6. Enemy list service, creation, subsequent updates/collision and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp','cpp/game/Movement.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-homing-native.py','tools/th16-shot-homing-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 homing callbacks.`);
