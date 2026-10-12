import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bomb-damage-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-bomb-damage-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm'),fixture='tests/cpp/th14-bomb-damage-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bomb-damage-native.json'),'utf8'));
for(const r of proof.direct)assert.equal(c.direct(r.selection),r.damage);
for(const r of proof.rows){assert.equal(c.run(...r.args),1,JSON.stringify(r.args));assert.equal(c.value(0),r.result[0]);assert.equal(c.value(1),r.result[2]);assert.equal(c.value(2),r.args[1]&&r.args[2]?1:0);}
for(const r of proof.circles){const why=JSON.stringify(r.args);assert.equal(c.circle(...r.args),1,why);assert.equal(c.value(0),r.result[0],why);assert.equal(c.value(1),r.result[1],why);assert.equal(c.value(2),r.args[3]?1:0,why);}
assert.equal(c.refusal(),1,'unsupported world delivery must still fail explicitly');
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,directCalls:proof.direct.length,collectorCases:proof.rows.length,bombCircleCases:proof.circles.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual six retail vtable +0xc methods return zero even for null/unmapped pointers; actual 451430 runs with all six active/inactive Bomb vtables, frame gates, empty pool or a ticking death circle. Actual 450130 allocation, Bomb bit set and 44e005 stationary clock feed actual 451430, compared against production ShotManager::th14_bomb_circle plus damage_th14 for Marisa B duration-zero circles, rectangle edge/miss cases and three rates before/after expiry. Damage and score are compared; native Bomb output flag is recorded but not exposed by this production fixture. Failed world delivery remains explicit. Controlled player/ANM/Bomb state. Does not verify Bomb startup, animation, time stop, cancellation, GPU pixels or full weapon behavior.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BombController.cpp','cpp/game/BombController.hpp','cpp/game/ShotTh14.cpp','cpp/game/ShotManager.cpp','cpp/game/ShotManager.hpp','cpp/game/ShotDamageTh14.cpp','cpp/game/ShotDamageTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bomb-damage-native.py','tools/th14-bomb-damage-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bomb-damage-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.directCalls} native virtual calls and ${report.collectorCases} production collector cases.`);
