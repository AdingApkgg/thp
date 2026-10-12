import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-state-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-bullet-state-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'bullets.wasm'),fixture='tests/cpp/th14-bullet-state-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-state-native.json'),'utf8')),table=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-table-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');assert.equal(sha(new Uint8Array(c.memory.buffer,c.table(),43*0x114)),table.tableSha256,'43 compiled native appearance records');
const state=()=>Array.from({length:proof.fields.length+3},(_,i)=>c.value(i)>>>0);
const spawned=()=>Array.from({length:c.spawn_count()},(_,i)=>Array.from({length:21},(_,j)=>c.spawn_word(i,j)>>>0));
for(const r of proof.cases){
 const label=`type ${r.type} color ${r.color} mode ${r.mode} rate ${r.rate}`;
 assert.equal(c.begin(r.type,r.color,r.mode,r.rate)>>>0,r.spawnStatus,label);assert.deepEqual(state(),r.spawn,label+' spawn');
 assert.deepEqual(spawned(),r.spawned,label+' spawn enemy requests');
 for(let frame=0;frame<r.frames.length;++frame){const row=r.frames[frame];assert.equal(c.tick(frame)>>>0,row.status,label+' frame '+frame);assert.deepEqual(state(),row.state,label+' frame '+frame);assert.deepEqual(spawned(),row.spawned,label+' frame '+frame+' enemy requests');}
}
const files=['cpp/game/BulletTh14.cpp','cpp/game/BulletTh14Launch.cpp','cpp/game/BulletManager.cpp','cpp/game/BulletState.hpp','cpp/game/Th14BulletTables.inc',fixture];
const report={passed:true,cases:proof.cases.length,frames:proof.cases.reduce((sum,r)=>sum+r.frames.length,0),appearanceRecords:43,enemySpawnTimelines:proof.cases.filter(r=>r.mode>=134).length,enemySpawnRequests:proof.cases.reduce((n,r)=>n+(r.frames.at(-1)?.spawned??r.spawned).length,0),nativeExecutableSha256:proof.executableSha256,
 normalizerDllSha256:proof.normalizerDllSha256,normalizerAddress:proof.normalizerAddress,
 scope:'Also includes ETEX 1000000 enemy creation immediately, after a wait, concurrent with acceleration and after position interpolation completes; compares all 84 request bytes and the request count after each full native update. Also includes ETEX 40000 immediate heading/speed, ETEX 80000 persistent polar displacement alone and concurrent, and ETEX 20000 position interpolation for all 32 modes, relative/absolute, zero/one duration, concurrent turn and sequential wait. Includes ETEX 100 offscreen holds and ETEX 1000 screen wrap in the production frame path, alone and concurrent with acceleration, wait and size interpolation. TH14 spawn and transforms 1/2/4/8/10/40/200/200000/400000/800000, concurrent acceleration/speed-ramp/turn/bounce and sequential completion, collision-delay/group/jump controls, wait/freeze countdowns, all seven stop/turn modes, saved position/angle and shared visual RNG state, primary appearance switching across all 43 types with optional interrupt, 32 size interpolation modes, timers, movement and scaled offscreen lifetime. Native ETEX 100 executes pinned D3DX9_43 SSE normalization under controlled CPU dispatch. Native ANM initialization/binding/update and collision are explicit controlled boundaries; WASM uses a fixed stop script, sprite dimensions and no-hit collision adapter. Native gameplay collision, secondary ANM, other transforms and GPU pixels remain unverified.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-state-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} TH14 bullet timelines, ${report.frames} frame states and 43 appearance records.`);
