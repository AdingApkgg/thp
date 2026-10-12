import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bomb-reward-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-bomb-reward-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-bomb-reward-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'reward.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bomb-reward-native.json'),'utf8')),f32=new Float32Array(1),u32=new Uint32Array(f32.buffer),toFloat=b=>{u32[0]=b;return f32[0]};
for(const [index,r] of proof.cases.entries()){
 const why=JSON.stringify({index,...r});assert.equal(c.begin(r.rewards,r.flags,r.count,r.seed,r.load,r.spawn,r.available,Number(r.ordinaryFull),...r.positionBits.map(toFloat)),0,why);
 assert.deepEqual(Array.from({length:4},(_,n)=>c.value(n)>>>0),r.result,why);
 for(let n=0;n<3;n++)assert.deepEqual(Array.from({length:14},(_,k)=>c.slot_value(n,k)>>>0),r.slots[n],`${why} slot ${n}`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/ItemManager.hpp','cpp/game/ItemManager.cpp','cpp/game/ItemTh14.cpp','cpp/game/BulletManager.hpp','cpp/game/BulletTh14.cpp','cpp/game/GameBattle.hpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 41ae00 reward types 0/1/2/3 and unknown type 4 versus production ItemManager. Signed wrapping reward/spawn counters, every-fifth ordinary power allocation, spell gating, single/double cancel items, full/one/two-slot pools, RNG consumption, delay thresholds and nonfinite/edge positions. Actual native ordinary factory and reward pool execute; ANM resource delivery is controlled. Complete Bomb animation, time freeze and damage geometry remain unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bomb-reward-native.py','tools/th14-bomb-reward-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bomb-reward-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} native Bomb reward cases.`);
