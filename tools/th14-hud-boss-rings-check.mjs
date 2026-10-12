import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-boss-rings-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-boss-rings-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-boss-rings-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'rings.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-boss-rings-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [n,r] of native.rows.entries()){
 assert.equal(c.run(r.variant,r.prior,r.position,r.displayed,r.hidden),1,`entry ${n}`);assert.deepEqual(Array.from({length:c.count()},(_,i)=>c.script(i)),r.created,`entry ${n} created`);
 assert.deepEqual([Boolean(c.name_value(0)),Boolean(c.name_value(1))],[r.nameRetained,r.nameRetired],`entry ${n} name`);
 for(const [slot,row] of r.observed.entries()){
  assert.deepEqual(Array.from({length:5},(_,k)=>c.state(slot,k)>>>0),row.state,`entry ${n} slot ${slot} state`);
  assert.deepEqual(Array.from({length:4},(_,k)=>c.mark(slot,k)>>>0),row.marks,`entry ${n} slot ${slot} marks`);
  for(const [i,vm] of row.vms.entries()){
   assert.equal(Boolean(c.present(slot,i)),vm!==null,`entry ${n} slot ${slot} vm ${i} presence`);
   if(vm){const expected=vm.slice();expected[0]&=6;assert.deepEqual(Array.from({length:7},(_,k)=>c.value(slot,i,k)>>>0),expected,`entry ${n} slot ${slot} vm ${i} words`);}
   assert.equal(Boolean(c.retired(slot,i)),r.retired[slot*7+i],`entry ${n} slot ${slot} vm ${i} retirement`);
  }
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/Hud.cpp','runtimes/th12/th12_web/cpp/game/Hud.hpp','runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','tools/th14-hud-boss-rings-native.py','tools/th14-hud-boss-rings-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-boss-rings-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production bosses_th14 uses synthetic stopped scripts, scalar states and seven VM flags/rotations/raw doubled position/pending words compared; real ANM geometry is a separate integration check.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} original two-boss ring cases exact`);
