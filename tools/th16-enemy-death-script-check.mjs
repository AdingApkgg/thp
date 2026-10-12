import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-death-script-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th16-enemy-death-script-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-enemy-death-script-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'death.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-death-script-native.json'),'utf8'));
for(const r of proof.cases){
 const data=Buffer.from(r.code,'hex'),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);
 assert.equal(c.run(p,data.length,r.threads,r.dirty),1,JSON.stringify(r));
 assert.deepEqual(Array.from({length:7},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));assert.equal(c.value(7),1);assert.equal(c.value(8),0);c.release(p);
}
// Unsupported death commands must retain the usual visible script error.
const bad=Buffer.alloc(32);bad.writeUInt16LE(557,4);bad.writeUInt16LE(16,6);bad[10]=255;bad.writeInt32LE(2147483647,16);bad.writeUInt16LE(16,22);bad[26]=255;
const p=c.allocate(bad.length);new Uint8Array(c.memory.buffer,p,bad.length).set(bad);assert.equal(c.run(p,bad.length,2,128),-2);assert.equal(c.value(5),0);c.release(p);
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/EnemyFrame.cpp','cpp/game/EnemyFrame.hpp','cpp/game/EnemyState.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp','cpp/game/EclOwner.cpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual own41d68a..41d6d9 death-subroutine consumer,41a4f0 secondary-context release,41a5a0 root reset and473bc0/472030 VM update at elapsed zero execute. Native name lookup and memory release are controlled. Production ECL556 copies its owned name, executes enemy_death after the controlled drop delivery, clears only the first name byte and resets the stack/threads.24 cases cover zero to three threads, dirty stacks and signed f32 locals. Unsupported557 propagates -2. Earlier sound/effect/drop/chapter operations, callbacks, natural stage progression and complete game excluded',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th16-enemy-death-script-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail death script cases.`);
