import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/shot-rewards-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-shot-rewards-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'rewards.wasm'),fixture='tests/cpp/th14-shot-rewards-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/shot-rewards-native.json'),'utf8'));let emissions=0;
for(const [i,r] of proof.rows.entries()){
 assert.equal(c.run(r.power,r.plain,r.focused,r.seed),1,`rewards ${i}`);assert.deepEqual(Array.from({length:5},(_,j)=>c.value(j)>>>0),r.result,`rewards ${i} state`);assert.equal(c.count(),r.requests.length);
 for(const [n,request] of r.requests.entries()){assert.deepEqual(Array.from({length:6},(_,j)=>c.request(n,j)>>>0),request,`rewards ${i} request ${n}`);++emissions;}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const [i,r] of proof.midpoints.entries()){
 const ptr=c.midpoint(...r.args),view=new DataView(c.memory.buffer);
 assert.deepEqual(Array.from({length:3},(_,j)=>view.getUint32(ptr+j*4,true)),r.result,`native wrapper midpoint ${i}`);
}
writeFileSync(resolve(root,'docs/porting/th14-shot-rewards-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,allocationAttempts:emissions,midpointCases:proof.midpoints.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 453a90 ordinary and focused counters, power-dependent deductions and actual visual RNG stream. Captures type 1/type 9 allocation attempts, positions/angles/speeds and manager spawn-count changes with full native item pools; allocation, ANM and item update are separate item proofs. Third +184bc counter stays zero. Production integrates ordinary/cancel item consumers; 64 actual 451760 wrapper calls also verify the damage-area/enemy midpoint before 453a90; the shot owner origin deliberately differs. The downstream callback is a sink; complete shot lifecycle remains unverified.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh14.cpp','cpp/game/ShotManager.hpp','cpp/game/GameBattle.hpp','cpp/game/ItemTh14.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-shot-rewards-native.py','tools/th14-shot-rewards-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.rows.length} shot reward timelines, ${emissions} allocation attempts, ${proof.midpoints.length} native wrapper midpoints.`);
