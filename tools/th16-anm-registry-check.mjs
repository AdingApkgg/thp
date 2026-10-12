import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/registry-check');mkdirSync(out,{recursive:true});
const python=process.env.TH_NATIVE_PYTHON;if(!python)throw Error('set TH_NATIVE_PYTHON');execFileSync(python,['tools/th16-anm-registry-native.py'],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/registry-native.json'),'utf8')),sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','AnmManager','Interpolation'].map(n=>`cpp/game/${n}.cpp`),fixture='tests/cpp/th16-anm-registry-fixture.cpp',wasm=resolve(out,'registry.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',...sources,fixture,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const row of proof.rows){const label=JSON.stringify(row);assert.equal(c.run(row.overlay,row.layer,row.state),0,label+' status');assert.equal(c.after_layer(),row.afterLayer,label+' layer');assert.equal(c.linked_layer(),row.links[0]??-1,label+' draw list');assert.equal(c.alive(),+!row.calls.includes('delete'),label+' retirement');assert.equal(row.count,row.links.length,label+' native count');}
const sha=b=>createHash('sha256').update(b).digest('hex'),tracked=[...sources,fixture,...['AnmVm','AnmOpcodes','AnmManager','AnmResource','AnmGeometry','AnmTrace','Interpolation','Timer','Types','Rng','PortTitle','Th16AnmDispatch'].map(n=>`cpp/game/${n}.hpp`)];
writeFileSync(resolve(root,'docs/porting/th16-anm-registry-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,scope:proof.scope,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(tracked.map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th16-anm-registry-check.mjs','tools/th16-anm-registry-native.py','tools/th-anm-handlers.py'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${proof.rows.length} native TH16 normal/overlay registry cases`);
