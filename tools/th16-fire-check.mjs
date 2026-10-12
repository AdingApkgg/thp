import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/fire-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-fire-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'fire.wasm'),fixture='tests/cpp/th16-fire-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/fire-native.json'),'utf8'));
for(const r of proof.positions){assert.equal(c.position(r.index,r.origin[2]),1);assert.deepEqual(Array.from({length:3},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.batches){assert.equal(c.batch(r.count,r.layers,r.flags,r.status,r.limit,...r.target.slice(0,2)),1);assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>Array.from({length:3},(_,field)=>c.event(n,field)>>>0)).map(row=>row[0]===0xffffffff?['sound',row[1],row[2]]:row),r.events,JSON.stringify(r));}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-fire-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,positions:proof.positions.length,batches:proof.batches.length,nativeExecutableSha256:proof.executableSha256,scope:'TH16 601 position/exclusion request with controlled414da0 boundary; full414da0 loops with controlled low-level spawn statuses 0/-1/1 and sound. Portable checks cover two position branches and production loop helper. Allocation/constructor/ETEX, sound queues and complete game are excluded. -2 is a port-only explicit unavailable operation error.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/BulletTh16.cpp','cpp/game/BulletTh16.hpp','cpp/game/BulletTh16Launch.cpp','cpp/game/BulletState.hpp','cpp/game/Th16BulletTables.inc','cpp/game/EnemyTh16Emitter.hpp','cpp/game/EnemyTh16Fire.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.positions.length} TH16 fire positions and ${proof.batches.length} batch loops`);
