import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/player-bullet-collision-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th14-player-bullet-collision-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-player-bullet-collision-fixture.cpp',wasm=resolve(out,'collision.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,'cpp/game/PlayerCollision.cpp','-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/player-bullet-collision-native.json'),'utf8')),f32=new Float32Array(1),u32=new Uint32Array(f32.buffer),toFloat=b=>{u32[0]=b;return f32[0]};
for(const [index,r] of proof.cases.entries()){const a=r.input.map((v,n)=>n>=1&&n<=8?toFloat(v):v);assert.equal(instance.exports.test(...a),r.result[0]|(r.result[1]<<8),JSON.stringify({index,...r}));}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/PlayerCollision.hpp','cpp/game/PlayerCollision.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail rectangle 44ee80 and circle 44efa0 versus production PlayerCollision: SSE edge/distance rounding, scaled radius, ordered/unordered comparisons, dialogue, probe, all player lifecycle states, invincibility and hit application. Native hit application is a recorded sink; complete game integration and laser geometry are separate.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-player-bullet-collision-native.py','tools/th14-player-bullet-collision-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-player-bullet-collision-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} native bullet collision cases.`);
