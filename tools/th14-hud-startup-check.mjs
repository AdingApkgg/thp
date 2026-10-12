import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-startup-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-startup-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-startup-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'startup.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-startup-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');let cases=0;
for(const [n,r] of native.rows.entries())for(const base of native.baseRows){
 assert.equal(c.run(r.stage,r.character,r.replay,r.continues,r.demo,r.prior,base.prior),1,`entry ${n}`);const expected=[...base.created,...r.created];assert.equal(c.count(),expected.length,`entry ${n} count`);
 for(const [i,v] of expected.entries())assert.deepEqual(Array.from({length:6},(_,k)=>c.value(i,k)>>>0),[v.script,v.flags,...v.position,v.rotation],`entry ${n} animation ${i}`);
 assert.equal(c.retained(0),Number(base.retained));assert.equal(c.retained(1),Number(r.retained));++cases;
}
for(const [n,r] of native.logoRows.entries()){
 assert.equal(c.logo_run(r.mode,r.flags),1,`logo ${n}`);assert.equal(c.count(),r.created.length,`logo ${n} count`);
 for(const [i,v] of r.created.entries())assert.deepEqual(Array.from({length:6},(_,k)=>c.value(i,k)>>>0),[v.script,v.flags,...v.position,v.rotation],`logo ${n} VM ${i}`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/Hud.cpp','runtimes/th12/th12_web/cpp/game/Hud.hpp','tools/th14-hud-startup-native.py','tools/th14-hud-startup-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-startup-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,baseEntries:native.baseRows.length,startupEntries:native.rows.length,combinedProductionCases:cases,logoCases:native.logoRows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production Hud::start_stage compares both block outputs across648 combinations with synthetic stopped ANM resources. '+native.logoScope,sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${cases} HUD startup / ${native.logoRows.length} logo combinations exact`);
