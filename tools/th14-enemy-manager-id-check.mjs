import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-manager-id-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-enemy-manager-id-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-enemy-manager-id-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'ids.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-manager-id-native.json'),'utf8'));
for(const [i,r] of proof.rows.entries()){assert.equal(c.initial_id(),r.result[0],`constructor ${i}`);assert.equal(c.reset_id(r.poison)>>>0,r.result[0],`reset ${i}`);assert.equal(r.result[1],0);assert.equal(r.registered,true);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-enemy-manager-id-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 4222f0 reset clears the manager, reserves ID zero, leaves count zero and registers the manager. CRT memset is a recording boundary. Production constructor/reset verify the resulting next ID and registration. Does not prove other manager fields, occupied-list teardown, constructor callbacks, ID overflow allocation or snapshot callback phase.',sourceHashes:Object.fromEntries([fixture,'cpp/game/EnemyManager.hpp','cpp/game/EnemyManager.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native manager ID resets and production initial IDs.`);
