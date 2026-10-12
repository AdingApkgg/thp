import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-boss-labels-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-boss-labels-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-boss-labels-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'labels.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-boss-labels-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const compare=(r,tag)=>{assert.equal(c.count(),r.created.length,`${tag} count`);for(const [i,v] of r.created.entries())assert.deepEqual(Array.from({length:6},(_,k)=>c.value(i,k)>>>0),[v.script,v.flags,...v.position,v.rotation],`${tag} creation ${i}`);};
for(const [n,r] of native.names.entries()){assert.equal(c.name_run(r.stage,r.section,r.spell,r.subtype,r.prior),1,`name ${n}`);compare(r,`name ${n}`);assert.equal(Boolean(c.retained()),r.retained,`name ${n} retained`);}
for(const [n,r] of native.markers.entries()){
 assert.equal(c.mark_run(r.remaining,r.pattern),1,`markers ${n}`);compare(r,`markers ${n}`);assert.deepEqual(Array.from({length:10},(_,i)=>Boolean(c.mark(i))),r.retained,`markers ${n} retained`);
 const labels=Array(10).fill(0);if(r.pattern!==3)for(const [handle,label] of r.interrupts)labels[handle-1]=label;
 assert.deepEqual(Array.from({length:10},(_,i)=>c.pending(i)),labels,`markers ${n} pending`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/Hud.cpp','runtimes/th12/th12_web/cpp/game/Hud.hpp','runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.cpp','tools/th14-hud-boss-labels-native.py','tools/th14-hud-boss-labels-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-boss-labels-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,names:native.names.length,markers:native.markers.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production methods use synthetic stopped front scripts; interruption pending checked on present old marker VMs, absent stale-handle interruption effects excluded.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.names.length} original boss-name / ${native.markers.length} remaining-marker cases exact`);
