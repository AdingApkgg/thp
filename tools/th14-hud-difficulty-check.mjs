import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-difficulty-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-difficulty-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-difficulty-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'difficulty.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-difficulty-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [n,r] of native.rows.entries()){
 assert.equal(c.run(r.difficulty,r.initial,r.prior,r.pending),1,`entry ${n}`);assert.equal(c.count(),r.created.length,`entry ${n} count`);
 for(const [i,v] of r.created.entries())assert.deepEqual(Array.from({length:7},(_,k)=>c.value(i,k)>>>0),[v.script,v.flags,...v.position,v.rotation,v.pending],`entry ${n} animation ${i}`);
 if(r.prior)assert.equal(c.old_pending()>>>0,r.oldPending,`entry ${n} old intro`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/Hud.cpp','tools/th14-hud-difficulty-native.py','tools/th14-hud-difficulty-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-difficulty-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,entries:native.rows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production Hud::start_stage uses synthetic stopped ANM resources to isolate these requests; unrelated startup animations excluded.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} original HUD difficulty entries exact`);
