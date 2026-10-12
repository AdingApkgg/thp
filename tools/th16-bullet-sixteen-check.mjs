import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/bullet-sixteen-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-bullet-sixteen-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'bullet-sixteen.wasm'),fixture='tests/cpp/th16-bullet-sixteen-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/bullet-sixteen-native.json'),'utf8'));
let maxError=0;
const floats=new Set([0,1,2,3,4,5,6,7,13,16,17,20,21,22,28,29,30,31,32]);
const decode=bits=>new Float32Array(new Uint32Array([bits]).buffer)[0];
function compare(expected,label){
 for(let i=0;i<33;i++){const actual=c.value(i)>>>0,wanted=expected.output[i];if(floats.has(i)){const error=Math.abs(decode(actual)-decode(wanted));maxError=Math.max(maxError,error);assert.ok(error<=.00004,`${label} field${i}: ${decode(actual)} != ${decode(wanted)}`);}else assert.equal(actual,wanted,`${label} field${i}`);}
 assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>Array.from({length:3},(_,f)=>c.event(n,f)>>>0)),expected.events,label);
}
for(const r of proof.cases){assert.equal(c.begin_case(r.rate,r.duration,r.index,r.concurrent,r.active,r.accel,r.direction,r.angle,r.sound,r.audio,r.mode,r.limit,r.spare,r.saved),0);compare(r.initial,`case${r.n} init`);for(let i=0;i<r.timeline.length;i++){assert.equal(c.step(),0,`case${r.n} frame${i}`);compare(r.timeline[i],`case${r.n} frame${i}`);}}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-bullet-sixteen-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,initializers:proof.cases.length,frames:proof.cases.length*64,maximumObservedFloatError:maxError,nativeExecutableSha256:proof.executableSha256,scope:'Modes 0 through 4. Full retail413860 initialization and411e70 state1 timelines with ETEX16/2048, saved position/angle/speed ETEX800000, optional concurrent ETEX1 and positional-audio2048 followed by same-call ETEX16 continuation. Retail415570 stop-and-turn motion,443840 aim from live or saved position,405340 bounded angle normalization,417510 polar vector, timers and same-frame continuation execute. Collision/ANM/audio/retirement are controlled services. Modes 5 through 7, other transforms, rendering and complete game excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/BulletTh16.cpp','cpp/game/BulletTh16.hpp','cpp/game/BulletState.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} TH16 ETEX16/2048 initializers / ${proof.cases.length*64} frames; max error ${maxError}`);

