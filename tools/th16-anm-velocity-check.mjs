import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/velocity-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-anm-velocity-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/velocity-native.json'),'utf8')),sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`),fixture='tests/cpp/th16-anm-velocity-fixture.cpp',wasm=resolve(out,'velocity.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',...sources,fixture,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const r of proof.rows){assert.equal(c.run(...r.slice(0,4)),0,`case ${r.slice(0,4)}`);assert.deepEqual(r.slice(4).map((_,i)=>c.word(i)>>>0),r.slice(4),`case ${r.slice(0,4)}`);}
const sha=b=>createHash('sha256').update(b).digest('hex'),tracked=[...sources,fixture,...['AnmVm','AnmOpcodes','AnmResource','AnmGeometry','AnmTrace','Interpolation','Timer','Types','Rng','PortTitle','Th16AnmDispatch'].map(n=>`cpp/game/${n}.hpp`)];
writeFileSync(resolve(root,'docs/porting/th16-anm-velocity-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,scope:proof.scope+' C++ runs the real update waiting on a synthetic future instruction; comparisons are confined to the seven velocity outputs and dirty flags.',nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(tracked.map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th16-anm-velocity-check.mjs','tools/th16-anm-velocity-native.py','tools/th-anm-handlers.py'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${proof.rows.length} native TH16 velocity/gate cases`);
