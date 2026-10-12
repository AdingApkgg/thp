import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/controller-input-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-controller-input-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['tests/cpp/th14-controller-input-fixture.cpp','cpp/game/GameInput.cpp'],wasm=resolve(out,'input.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/controller-input-native.json'),'utf8'));
for(const r of proof.cases){const cfg=Buffer.from(r.config,'hex'),buttons=Buffer.from(r.buttons,'hex'),p=c.allocate(cfg.length+buttons.length);try{new Uint8Array(c.memory.buffer,p,cfg.length).set(cfg);new Uint8Array(c.memory.buffer,p+cfg.length,buttons.length).set(buttons);assert.equal(c.sample(r.held,p+cfg.length,buttons.length,r.x,r.y,p)>>>0,r.result,JSON.stringify(r));}finally{c.release(p);}}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-controller-input-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 4018b0 successful DirectInput path. Controlled device poll/state delivery, actual four-action mapping, byte high-bit tests, disabled/duplicate/127..124 bindings, preserved held bits and signed deadzone boundaries at config 18/1a. Extra controller entries 8/9 do not produce a fifth action. WinMM path, polling failures, keyboard sampling, remapping UI and whole game remain outside this proof.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} retail DirectInput samples.`);
