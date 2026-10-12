import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-spawn-check');mkdirSync(out,{recursive:true});
execFileSync('py',['-3','tools/th14-enemy-spawn-native.py'],{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyState.cpp','cpp/game/EclContext.cpp','cpp/game/Movement.cpp','cpp/game/Interpolation.cpp','tests/cpp/th14-enemy-spawn-fixture.cpp'],wasm=resolve(out,'spawn.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-spawn-native.json'),'utf8'));
for(const row of proof.cases){const b=Buffer.from(row.code,'hex'),p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);try{assert.equal(c.run_case(p,row.flags,row.parent-123),1);assert.deepEqual(Array.from({length:21},(_,n)=>c.value(n)>>>0),row.output,JSON.stringify(row));}finally{c.release(p);}}
for(const row of proof.modes){assert.equal(c.mode_value(row.value,0)>>>0,row.integer);assert.equal(c.mode_value(row.value,1)>>>0,row.floating);}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.cases.length,modeGlobals:proof.modes.length,nativeExecutableSha256:proof.executableSha256,scope:'Retail 42a1e0 two-dimensional spawn descriptors, relative/absolute and mirrored positions, local argument references and inherited fields, plus -9907 integer/float mode getters. Native entity allocation, limits, constructor and complete enemy frame semantics remain separate.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EnemyManager.cpp','cpp/game/EnemyManager.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-enemy-spawn-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} TH14 spawn descriptors.`);
