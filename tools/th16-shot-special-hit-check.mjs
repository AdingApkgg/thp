import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-special-hit-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-special-hit-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-special-hit-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'special.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-special-hit-native.json'),'utf8'));let maxError=0;
const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,kind:r.kind,seed:r.seed});assert.equal(c.begin(r.kind,r.seed),1,why);
 const compare=(v,w,label)=>{assert.equal(v.length,w.length,why+label);for(let k=0;k<v.length;k++){if(v[k]===w[k])continue;const error=Math.abs(f(v[k])-f(w[k]));maxError=Math.max(maxError,error);assert.ok(Number.isFinite(error)&&error<=.001,why+label+` field${k}: ${v[k]} / ${w[k]}, error${error}`);}};
 const output=Array.from({length:r.output.length},(_,k)=>c.value(k)>>>0);
 for(let k=0;k<r.output.length;k++)if(r.kind||k<3)assert.equal(output[k],r.output[k],why+` field${k}`);compare(output,r.output,'output');
 assert.equal(c.count(),r.events.length,why+'count');for(let n=0;n<r.events.length;n++){const ev=r.events[n],got=Array.from({length:ev.length},(_,k)=>c.event(n,k)>>>0);for(let k=0;k<ev.length;k++)if(k<3||k===7)assert.equal(got[k],ev[k],why+'event'+n+'/'+k);compare(got,ev,'event');}
 compare(Array.from({length:r.interp.length},(_,k)=>c.interp(k)>>>0),r.interp,'interp');
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-special-hit-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Complete446870 beam hit and447320 freeze hit. Original404600 geometry, trig, sqrt, RNG,447550 scale interpolation,4173f0 position interpolation and445e20 default hit execute. ANM creation/lookup/family interrupt and effect registration controlled; successful allocation only. Geometry/effect float tolerance .001; counters, RNG seed/calls, colors, scale and default hit exact. Original pixels, allocator and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16Hit.cpp','cpp/game/ShotTh16Geometry.cpp','cpp/game/ShotTh16.hpp','cpp/game/ShotTh16Production.cpp','cpp/game/ShotManager.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-special-hit-native.py','tools/th16-shot-special-hit-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 special hits.`);
