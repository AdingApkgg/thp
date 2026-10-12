import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-update-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-update-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-update-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'update.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-update-native.json'),'utf8'));
let maxError=0;const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
function compare(actual,expected,float,why){if(!float){assert.equal(actual,expected,why);return;}const error=Math.abs(f(actual)-f(expected));maxError=Math.max(maxError,error);assert.ok(error<=.00004,why+` error${error}`);}
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,state:r.state,age:r.age,kind:r.kind,callback:r.callback,flags:r.flags,flags2:r.flags2,missing:r.missing,geometry:r.geometry,rate:r.rate});assert.equal(c.begin(r.state,r.age,r.kind,r.callback,r.flags,r.flags2,r.missing,r.geometry,-.75,6.25,r.rate),1,why);
 for(let k=0;k<13;k++)compare(c.value(k)>>>0,r.output[k],k===10||k===11,why+` state${k}`);
 for(let k=0;k<8;k++)compare(c.movement(k)>>>0,r.movement[k],k===0||k===1||k===5||k===6,why+` movement${k}`);
 for(let k=0;k<37;k++)compare(c.area(k)>>>0,r.area[k],k===7||k===8,why+` area${k}`);
 assert.deepEqual(Array.from({length:c.count()},(_,n)=>Array.from({length:4},(_,k)=>c.event(n,k)>>>0)),r.events,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-update-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Complete4456d0 executes across256 slots with occupied index0/255. Native402ff0/403110 and447480 execute. State1/2, callback0/5/controlled nonzero skip, 15-frame geometry boundary/strict playfield edges/one visible corner, type2 geometry bypass, stale ANM, source sync conditional flags1, retirement, flag80 rotation/world position, timers/rates and preserved z velocity. ANM lookup/geometry/delete and security cookie controlled. Float tolerances4e-5 only propagate x87 trig differences. Movement modes1-4, resource callback dispatch/beam update, original pixels, damage collision and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp','cpp/game/Movement.cpp','cpp/game/AnmGeometry.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-update-native.py','tools/th16-shot-update-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 complete shot updates.`);
