import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/config-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-config-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-config-fixture.cpp','cpp/game/GameConfig.cpp'],wasm=resolve(out,'config.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/config-native.json'),'utf8'));let defaults;
for(const r of proof.cases){const b=Buffer.from(r.data,'hex'),p=c.allocate(b.length);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);assert.equal(c.check(p,r.size),Number(r.accepted),JSON.stringify(r));const result=Buffer.from(new Uint8Array(c.memory.buffer,c.data(),92));if(r.accepted)assert.deepEqual(result,b);else{defaults??=result;assert.deepEqual(result,defaults);}}finally{c.release(p);}}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-config-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 4454b8..4454ff option/signature/size branch: all byte values for six fields 1c..21, signature and buffer-size boundaries. Production accepts identical buffers and leaves initialized defaults on rejection. Native filesystem, startup reset/log delivery, controller input consumption and whole game are outside this validation proof.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} native configuration validations.`);
