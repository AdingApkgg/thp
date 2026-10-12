import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bomb-child-position-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-bomb-child-position-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-sakuya-b-controller-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'position.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bomb-child-position-native.json'),'utf8')),ptr=c.allocate(4*12*4);
for(const [i,r] of proof.cases.entries())for(const spell of [0,1,0x23]){
 new Uint32Array(c.memory.buffer,ptr,r.records.length*12).set(r.records.flat());assert.equal(c.marisa_a_child(ptr,r.records.length,spell),1,`${i} ${spell}`);assert.equal(c.event_count(),1,`${i} ${spell} requests`);
 assert.deepEqual(Array.from({length:c.event_size(0)},(_,j)=>c.event(0,j)>>>0),[8,...r.position,0x42700000,0x43c80000,0xbfc90fdb,+( !(spell&1))],`${i} ${spell}`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,nativeCases:proof.cases.length,cancelRequests:proof.cases.length*3,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual recursive 412c60 versus production BombController selection-2 script-26 cancellation request. One to four ancestors, inheritance/rotation flags, parent angles, finite float cancellation/rounding and signed zeros. Size 48*scale.x / 160*scale.y and spell-controlled reward request compared. ANM scripts and delivery controlled; no laser-cut, geometry or pixels claim.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BombController.cpp','cpp/game/BombController.hpp','cpp/game/AnmManager.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bomb-child-position-native.py','tools/th14-bomb-child-position-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bomb-child-position-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.nativeCases} native positions / ${report.cancelRequests} production requests.`);
