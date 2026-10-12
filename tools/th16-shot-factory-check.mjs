import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-factory-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-factory-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-factory-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'factory.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-factory-native.json'),'utf8'));
let maxError=0;const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
function compare(actual,expected,float,why){if(!float){assert.equal(actual,expected,why);return;}const error=Math.abs(f(actual)-f(expected));maxError=Math.max(maxError,error);assert.ok(error<=.00004,why+` error${error}`);}
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,number:r.number,kind:r.kind,angle:r.angle,focus:r.focus,family:r.family,callback:r.callback,flags2:r.flags2,cursor:r.cursor,sound:r.sound});assert.equal(c.begin(r.number,r.kind,r.angle,r.focus,r.family,r.callback,r.flags2,r.cursor,r.sound)>>>0,r.result,why);
 for(let k=0;k<37;k++)compare(c.value(k)>>>0,r.output[k],k===18||k===19,why+` state${k}`);
 for(let k=0;k<8;k++)compare(c.movement(k)>>>0,r.movement[k],k===0||k===1||k===5||k===6,why+` movement${k}`);
 for(let k=0;k<37;k++)compare(c.area(k)>>>0,r.area[k],k===7||k===8,why+` area${k}`);
 assert.equal(c.count(),r.events.length,why);for(let n=0;n<r.events.length;n++)for(let k=0;k<4;k++)compare(c.event(n,k)>>>0,r.events[n][k],r.events[n][0]===3&&k===2,why+` event${n}/${k}`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-factory-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Full444e10 and444b20 execute, native445ed0/446200/447450 execute. Both families, main script+5/season raw, option offsets, focus bits, beam cache, RNG, damage rectangle initialization and timer, allocation cursor wrap, callbacks0/1/2/4 and controlled rejection cleanup, beam sound20/period1/width0/shot flag clear, Cirno source callback2, raw-angle VM rotation flag80, positional sound24 and final world position. Native ANM406380/lookup/delete and audio are controlled boundaries. Float tolerances4e-5 only propagate native x87 trig differences. Native pool exhaustion, subsequent movement/collision and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp','cpp/game/ShotTh16Production.cpp','cpp/game/ShtResource.cpp','cpp/game/AnmManager.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-factory-native.py','tools/th16-shot-factory-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 complete shot factories.`);
