import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/boss-interrupt-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-boss-interrupt-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'boss.wasm'),fixture='tests/cpp/th14-boss-interrupt-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/boss-interrupt-native.json'),'utf8'));
for(const r of proof.cases)for(const refs of [0,1]){
 assert.equal(c.run(r.selected,r.callerSlot,r.pattern,r.mode,r.threads,refs),0,JSON.stringify(r));
 assert.deepEqual(Array.from({length:24},(_,n)=>c.word(n)>>>0),r.states.flat(),JSON.stringify({...r,refs}));
 assert.equal(r.freeCount,r.lookupCount*r.threads*2);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-boss-interrupt-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length*2,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'ECL 802 retail 429a9e..429c28 executes actual 421120 secondary release, 4211c0 root reset and 484b80 selection. Argument read, deallocation and name lookup are controlled boundaries. Three boss slots, caller-slot exclusion, absent owners, negative health, absent names, eight-slot range samples and zero/two secondary contexts are covered. Production dispatch uses real EnemyManager and ECL owners with immediate/local references; script selection does not execute the new subroutine or consume the interrupt. Invalid indices are rejected by the port rather than reading outside retail storage. Native lookup implementation, future script execution, actual gameplay and GPU pixels are outside scope.',sourceHashes:Object.fromEntries([fixture,'cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp','cpp/game/EclOwner.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-boss-interrupt-native.py','tools/th14-boss-interrupt-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS: ${proof.cases.length*2} native boss interrupt cases.`);
