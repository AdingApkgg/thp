import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/item-drop-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-item-drop-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-item-drop-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'drop.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/item-drop-native.json'),'utf8'));let maxError=0;
const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,seed:r.seed});assert.equal(c.begin(r.seed),1,why);assert.deepEqual(Array.from({length:20},(_,k)=>c.value(k)>>>0),r.output,why);assert.equal(c.count(),r.events.length,why);
 for(let n=0;n<r.events.length;n++)for(let k=0;k<7;k++){const actual=c.event(n,k)>>>0,expected=r.events[n][k];if(k===1||k===2){const error=Math.abs(f(actual)-f(expected));maxError=Math.max(maxError,error);assert.ok(error<=.00004,why+` event${n}/${k} ${error}`);}else assert.equal(actual,expected,why+` event${n}/${k}`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-item-drop-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Full420585 ECL509,41a720 drop and41d700 scatter. Original RNG402cb0/402c70/402cf0,426240 anisotropic trig and memset execute. Practice skip, time-scaled season count, nonzero primary,16 extra kinds, kind16 special speed/angle sequence,17 counts clear, native visual RNG seed/calls/order. Factory430960 controlled; original factories, death-path caller and full gameplay excluded. Ordinary position tolerance4e-5; remaining fields exact.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ItemTh16Drop.cpp','cpp/game/ItemManager.hpp','cpp/game/EnemyTh16Commands.cpp','cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-item-drop-native.py','tools/th16-item-drop-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 ECL509/scatter cases.`);
