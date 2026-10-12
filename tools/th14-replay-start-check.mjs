import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/replay-start-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-replay-start-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-replay-start-fixture.cpp',sources=[fixture,'cpp/game/Replay.cpp','cpp/game/ReplayRecorder.cpp','cpp/game/ResourceCrypt.cpp','cpp/game/Lzss.cpp'],path=resolve(out,'start.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',...sources,'-o',path],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/replay-start-native.json')));
for(const row of proof.rows){const header=Buffer.from(row.header,'hex');new Uint8Array(c.memory.buffer,c.input_header(),header.length).set(header);assert.equal(c.capture(),1);assert.deepEqual(Buffer.from(new Uint8Array(c.memory.buffer,c.output_header(),header.length)),header,`native activation header stage${row.stage} seed${row.seed}`);}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-replay-start-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,scope:proof.scope+' Production ReplayRecorder.start_stage later-entry headers compared byte-for-byte with the native activation output.',wasmSha256:sha(bytes),sources:Object.fromEntries([...sources,'cpp/game/Replay.hpp','cpp/game/ReplayRecorder.hpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),tools:Object.fromEntries(['tools/th14-replay-start-native.py','tools/th14-replay-start-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${proof.rows.length} complete native activation header comparisons`);
