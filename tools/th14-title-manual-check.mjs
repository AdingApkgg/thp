import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/title-manual-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-title-manual-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-title-manual-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'manual.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/title-manual-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [n,r] of native.rows.entries()){
 assert.equal(c.run(r.substate,r.timer,r.asciiPresent,r.finished),1,`entry${n}`);const state=[...r.state];state[2]++;
 assert.deepEqual(Array.from({length:5},(_,k)=>c.value(k)>>>0),state.map(Number),`entry${n} state`);
 assert.deepEqual(Array.from({length:c.count()},(_,i)=>[c.binding(i,0),c.binding(i,1)]),r.bindings,`entry${n} bindings`);
 assert.equal(c.value(5),Number(r.services.includes('create_help')));assert.equal(c.value(6),Number(r.services.includes('destroy_help')));assert.equal(c.value(7)>>>0,r.helpOrigin);
 for(const [handle,signal] of r.labels)if(handle)assert.equal(c.label(handle===119?0:1),signal,`entry${n} exit label`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/TitleMenu.hpp','runtimes/th12/th12_web/cpp/game/TitleMenu.cpp','runtimes/th12/th12_web/cpp/game/TitleTh14.cpp','tools/th14-title-manual-native.py','tools/th14-title-manual-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-title-manual-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production TitleMenu::update compares service requests/state/retained handles/create scripts/actual existing-root exit interrupts using synthetic ANM resources. Includes the production outer timer tick(+1), matching the native caller boundary after461d10; nonexistent-handle interrupt effects excluded.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${native.rows.length} title Manual entry/wait/exit cases exact`);
