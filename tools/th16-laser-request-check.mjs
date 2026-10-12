import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/laser-request-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-laser-request-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'requests.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',...['allocate','release','request'].map(n=>'-Wl,--export='+n),'-Wl,-z,stack-size=1048576','-DPORT_TITLE=16','tests/cpp/th16-laser-request-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/laser-request-native.json'),'utf8'));
const p=c.allocate(0x39c0),pos=c.allocate(12),request=c.allocate(0x358);
for(const [n,r] of proof.cases.entries()){new Uint8Array(c.memory.buffer,p,0x39c0).set(Buffer.from(r.initial,'hex'));new Uint32Array(c.memory.buffer,pos,3).set(r.positionBits);assert.equal(c.request(p,r.index,pos,request),1,`request ${n}`);assert.equal(Buffer.from(new Uint8Array(c.memory.buffer,request,0x358)).toString('hex'),r.request,`whole request ${n}`);assert.deepEqual(r.reads,[0]);}
for(const a of [p,pos,request])c.release(a);
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th16-laser-request-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length,requestBytes:0x358,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own421912 ECL702 complete request preparation, normalized angle, origin branches, full18 ETEX records, sounds, flags and unchanged emitter state. Factory431760 controlled. Production helper only; actual TH16 laser allocation/update/collision/cancel/render still pending.',sourceHashes:Object.fromEntries(['cpp/game/EnemyTh16Fire.cpp','cpp/game/EnemyCommands.hpp','tests/cpp/th16-laser-request-fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');console.log(`PASS ${proof.cases.length} whole0x358 own TH16 laser requests`);
