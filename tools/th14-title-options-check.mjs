import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/title-options-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-title-options-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
nativePython('tools/th14-title-unlock-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-title-options-fixture.cpp',path=resolve(out,'title-options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const resource=readFileSync(resolve(root,'artifacts/archive-differential/th14-bBPoO0/title.anm')),p=c.allocate(resource.length);new Uint8Array(c.memory.buffer,p,resource.length).set(resource);assert.equal(c.open(p,resource.length),1);c.release(p);
const ascii=readFileSync(resolve(root,'artifacts/archive-differential/th14-bBPoO0/ascii.anm')),ap=c.allocate(ascii.length);new Uint8Array(c.memory.buffer,ap,ascii.length).set(ascii);assert.equal(c.open_ascii(ap,ascii.length),1);c.release(ap);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/title-options-native.json'),'utf8'));
for(const [index,row] of proof.rows.entries()){
 const ok=c.run(row.bgm,row.sound),mem=new Uint8Array(c.memory.buffer),ep=c.error();
 assert.equal(ok,1,`case${index}: ${new TextDecoder().decode(mem.subarray(ep,mem.indexOf(0,ep)))}`);
 for(const [script,sprite] of row.bindings)assert.equal(c.value(script,0)>>>0,sprite,`case${index} sprite script${script}`);
 for(const [script,visible] of row.visible)assert.equal(c.value(script,1),+visible,`case${index} visibility script${script}`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const unlock=JSON.parse(readFileSync(resolve(root,'artifacts/th14/title-unlock-native.json'),'utf8'));
for(const [index,row] of unlock.rows.entries()){
 c.set_clear(row.selection,row.difficulty,row.flag,row.prefs);
 assert.deepEqual(Array.from({length:6},(_,s)=>c.available(s)),row.available,`eligibility${index}`);
 assert.equal(c.unlocked(),row.unlocked,`unlock${index}`);
}
writeFileSync(resolve(root,'docs/porting/th14-title-unlock-verified.json'),JSON.stringify({passed:true,cases:unlock.rows.length,nativeExecutableSha256:unlock.executableSha256,wasmSha256:sha(bytes),scope:'Native4591d0/459220 unmodified with controlled seven CR records/ST bytes, versus production TitleMenu::available/unlocked. All six equipment choices, four normal difficulties, Extra/aggregate exclusion, nonzero flag values and unrelated legacy preference bytes. Does not prove clear-flag generation or completion/ending.',sourceHashes:Object.fromEntries([fixture,'cpp/game/TitleMenu.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-title-unlock-native.py','tools/th14-title-options-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
writeFileSync(resolve(root,'docs/porting/th14-title-options-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,resourceSha256:sha(resource),wasmSha256:sha(bytes),scope:'Complete native45b870 digit binding/visibility versus production TitleMenu::options initialization with retail title.anm. Includes all256 incoming raw values in each volume byte and threshold combinations. Native ANM lookup/binding/child lookup and audio delivery are controlled; resource interpreter/GPU pixels, menu layout interrupts and audio volume are not proved by this fixture.',sourceHashes:Object.fromEntries([fixture,'cpp/game/TitleOptions.cpp','cpp/game/TitleMenu.cpp','cpp/game/GameConfig.hpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-title-options-native.py','tools/th14-title-options-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} native TH14 volume display cases on retail title.anm`);
