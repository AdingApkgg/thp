import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-beam-update-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-beam-update-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-beam-update-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'beam.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-beam-update-native.json'),'utf8'));let maxError=0;
const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,seed:r.seed});assert.equal(c.begin(r.seed),1,why);assert.deepEqual(Array.from({length:13},(_,k)=>c.value(k)>>>0),r.output,why);
 for(let k=0;k<37;k++){const value=c.area(k)>>>0;if(k===7||k===8){const error=Math.abs(f(value)-f(r.area[k]));maxError=Math.max(maxError,error);assert.ok(error<=.00004,why+` area${k} error${error}`);}else assert.equal(value,r.area[k],why+` area${k}`);}
 assert.deepEqual(Array.from({length:c.count()},(_,n)=>[c.event(n,0)>>>0,c.event(n,1)>>>0]),r.events,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-beam-update-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Complete446260, original4476b0 trig executes. Both option families/fixed-point locations, near .001 angle smoothing versus snap/focus -pi/2, state2 early return, pan,512/18 length growth, own area center, VM flags/sprite size/texture scale, hit marker interrupt3, firing/count/life2/4/power cache/dialogue/manager gates, simultaneous interrupts3/1, cache clear and channel20 stop. ANM lookup/family interrupt and audio virtual/stop controlled; all occupied-area words exact except4e-5 native trig center tolerance. Beam hit callback, actual audio and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp','cpp/game/ShotTh16Production.cpp','cpp/game/ShotManager.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-beam-update-native.py','tools/th16-shot-beam-update-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 beam updates.`);
