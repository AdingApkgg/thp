import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-enemy-spawn-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-bullet-enemy-spawn-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'bullet-enemy-spawn.wasm'),fixture='tests/cpp/th14-bullet-enemy-spawn-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-enemy-spawn-native.json'),'utf8'));
for(const [i,r] of proof.setters.entries()){
 const code=Buffer.from(r.code,'hex'),p=c.allocate(code.length);new Uint8Array(c.memory.buffer,p,code.length).set(code);
 try{assert.equal(c.setter(p,code.length),0,`setter ${i}`);assert.deepEqual(Buffer.from(c.memory.buffer,c.output(),0x3800),Buffer.from(r.result,'hex'),`setter ${i} all emitter bytes`);assert.equal(c.cursor(r.emitter),r.cursor,`setter ${i} cursor`);assert.deepEqual(r.reads,[0,1]);}finally{c.release(p);}
}
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.begin(r.index,r.active,r.concurrent,i%8),0,`dispatcher ${i}`);assert.deepEqual([c.state(0),c.state(1)].map(x=>x>>>0),r.state,`dispatcher ${i} gates`);assert.equal(c.calls(),r.records.length);
 if(r.records.length){const bytes=new Uint8Array(c.memory.buffer,c.name(),64);assert.equal(new TextDecoder().decode(bytes.subarray(0,bytes.indexOf(0))),r.records[0].name);assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,c.descriptor(),21)),r.records[0].descriptor,`dispatcher ${i} descriptor`);}
}
for(const [i,r] of proof.cases.entries()){
 assert.equal(c.consume(r.index,r.active,r.concurrent,i%8),0,`consumer ${i}`);
 const expected=Array(25).fill(0);expected[1]=1;
 if(r.records.length){const d=r.records[0].descriptor;expected.splice(0,25,1,2,1,...d.slice(0,3),d[5],...d.slice(8,20),d[3],d[4],d[20],1,0x3f800000,1);}
 assert.deepEqual(Array.from({length:25},(_,n)=>c.consumer_word(n)>>>0),expected,`consumer ${i} actual ECL factory, first frame and ID`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');const sources=[fixture,'cpp/game/BulletTh14.cpp','cpp/game/EnemyTh14Emitter.cpp','cpp/game/BulletState.hpp','cpp/game/BulletManager.hpp','cpp/game/GameBattle.hpp','cpp/game/EnemyManager.cpp'];
const report={passed:true,setters:proof.setters.length,cases:proof.cases.length,consumers:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail ECL640 writer 4285af and full ETEX1000000 dispatcher 418140. Compares all sixteen emitter descriptors with pointer normalized to instruction offset, cursor retention, all 84 spawn descriptor bytes, subroutine name, active/concurrent gates and transform index advancement. Native argument getters, memset and enemy factory are recorded boundaries. The original ignores factory return. Canonical callback failure remains a diagnostic error for an unavailable external operation; Also executes the real ECL640 producer -> BulletManager bridge -> EnemyManager factory with a minimal named ECL program, checking created IDs, first-frame execution/clocks, position and all eight arguments. Native constructor internals and full original-resource sessions remain separate proofs.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-bullet-enemy-spawn-native.py','tools/th14-bullet-enemy-spawn-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-enemy-spawn-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.setters.length} original ECL640 name writers and ${proof.cases.length} enemy transform dispatch cases.`);
