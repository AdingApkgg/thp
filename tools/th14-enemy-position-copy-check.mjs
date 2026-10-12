import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-position-copy-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-enemy-position-copy-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-enemy-position-copy-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'copy.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-position-copy-native.json'),'utf8'));
const put=words=>{const p=c.allocate(Math.max(words.length,1)*4);if(words.length)new Uint32Array(c.memory.buffer,p,words.length).set(words);return p;};
for(const [index,r] of proof.cases.entries()){
 const initial=put(r.initial),records=put(r.records.flat());try{
  assert.equal(c.begin(r.op,r.id,initial,records,r.records.length),r.found?0:-2,`case ${index}`);
  assert.deepEqual(Array.from({length:52},(_,n)=>c.value(n)>>>0),r.result,`state ${index}`);
 }finally{c.release(initial);c.release(records);}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyState.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 421aa0 list lookup and ECL 432/433 copying current raw XYZ into absolute/relative movement, with no immediate combine or mode/velocity reset. Includes duplicate IDs (first match), unmatched nonzero IDs (last visited entry), list sizes 0..4, signed IDs, NaNs and signed zero payloads; production ECL variable-reference dispatch is used by the port. Native argument selection is a controlled wrapper calling actual 42a920 integer global getter for -9909 (parent ID); the port exercises that same reference. Native zero-ID/empty-list lookup returns null and subsequent command would crash; the port explicitly rejects that dereference without mutation. Manager spawn ordering, full native ECL VM, remaining movement commands and complete gameplay are unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-enemy-position-copy-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail enemy position copy/lookup cases.`);
