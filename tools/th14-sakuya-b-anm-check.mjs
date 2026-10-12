import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/sakuya-b-anm-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-sakuya-b-anm-native.py',{cwd:root,stdio:'inherit',windowsHide:true});execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-sakuya-b-anm-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'anm.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const [which,name] of ['pl02.anm','ascii.anm'].entries()){const data=readFileSync(resolve(root,'artifacts/archive-differential/th14-bBPoO0',name)),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open(p,data.length,which),1);}
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/sakuya-b-anm-native.json'),'utf8'));let frames=0;
for(const r of proof.rows){assert.deepEqual(r.children,r.slot===21?[22]:[]);for(const [n,f] of r.frames.entries()){assert.equal(n?c.tick():c.begin(r.slot,r.rate),f.status,`${r.slot} ${r.rate} ${n}`);assert.deepEqual(Array.from({length:14},(_,k)=>c.value(k)>>>0),f.state.map(v=>v>>>0),`${r.slot} ${r.rate} ${n}`);++frames;}}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/AnmVm.cpp','cpp/game/AnmInterpreter.cpp','cpp/game/AnmManager.cpp','cpp/game/AnmGeometry.cpp','cpp/game/AnmResource.cpp'];
const report={passed:true,frames,nativeExecutableSha256:proof.executableSha256,resourceSha256:proof.resourceSha256,wasmSha256:sha(bytes),scope:'Full native interpreter versus production on retail pl02.anm scripts 20/21/22 through termination at rates .5/1/1.25: sprite, color, layer, resolution flags, active bit, clock, position, scale and extra scale. Native sprite binding and child creation are controlled; script-21 request for child 22 is checked and script 22 is independently executed. No GPU/pixel or full Bomb-controller equivalence is claimed.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-sakuya-b-anm-native.py','tools/th14-sakuya-b-anm-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-sakuya-b-anm-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${frames} Sakuya B original ANM frames.`);
