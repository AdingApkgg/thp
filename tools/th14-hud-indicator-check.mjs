import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-indicator-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-indicator-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-indicator-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'indicator.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-indicator-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [n,r] of native.rows.entries()){
 assert.equal(c.run(r.present,r.flags,r.mode,r.spell,r.value,r.x,r.playerX,r.children),1,`entry ${n}`);assert.deepEqual(Array.from({length:6},(_,k)=>c.value(k)>>>0),r.state,`entry ${n} state`);
 assert.deepEqual([Boolean(c.value(6)),Boolean(c.value(7))],r.childVisible,`entry ${n} children`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/Hud.cpp','runtimes/th12/th12_web/cpp/game/Hud.hpp','runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','tools/th14-hud-indicator-native.py','tools/th14-hud-indicator-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-indicator-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production indicator_th14 uses synthetic stopped front111 and two child VMs; all state/position/alpha/pending words and visibility compared.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} original indicator cases exact`);
