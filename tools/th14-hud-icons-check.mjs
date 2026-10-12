import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-icons-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-hud-icons-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-icons-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'icons.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const source='artifacts/archive-differential/th14-bBPoO0/front.anm',data=readFileSync(resolve(root,source)),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open(p,data.length),1);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-icons-native.json'),'utf8'));let frames=0;
for(const r of proof.rows){assert.equal(c.begin(),1);const n=r.slot-29;
 for(const [frame,row] of r.frames.entries()){
  if(frame){if(r.schedule[frame]!==undefined)c.signal(n,r.schedule[frame]);assert.equal(c.tick(),1);assert.equal(c.layer_count(),16);}
  assert.deepEqual(Array.from({length:10},(_,k)=>c.value(n,k)>>>0),row.map(v=>v>>>0),`script ${r.slot}, early=${r.early}, frame ${frame}`);++frames;
 }
}
// Exercise production stock delivery and layer rendering with retail sprites.
assert.equal(c.begin(),1);c.display(2,1,3,4);assert.deepEqual(Array.from({length:16},(_,n)=>c.pending(n)),[2,2,8,3,3,3,3,3,2,2,2,10,3,3,3,3]);
for(let i=0;i<120;i++)assert.equal(c.tick(),1);assert.equal(c.layer_count(),16);
assert.equal(c.draw_icons(),96,'all sixteen icons must submit their six screen vertices');
for(let n=0;n<96;n++){const x=c.vertex(n,0),y=c.vertex(n,1);assert.ok(x>=504&&x<=640&&y>=96&&y<=160,`HUD vertex ${n}: ${x},${y}`);}
assert.equal(c.clear_hud(),0,'HUD destruction must unregister the manager-owned icon VMs');assert.equal(c.layer_count(),0);
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=[fixture,'cpp/game/Hud.hpp','cpp/game/Hud.cpp','cpp/game/AnmManager.cpp','cpp/game/AnmVm.cpp','cpp/game/AnmInterpreter.cpp','cpp/game/AnmResource.cpp','cpp/game/AnmGeometry.cpp','cpp/game/AnmRenderer.cpp','cpp/game/SceneSchedule.hpp'];
const report={passed:true,frames,icons:16,renderVertices:96,nativeExecutableSha256:proof.executableSha256,resourceSha256:sha(data),wasmSha256:sha(bytes),scope:'Retail front.anm scripts 29..44 execute through the full native 46fe50 interpreter for 181 frames each, with immediate/delayed stock interrupts, all fragment labels, RGB, alpha fades, clocks, layer and resolution flags, local position bits. Security-cookie check and sprite resource bind are controlled native boundaries. Production Hud manager registration, once-per-tick updates, layer 24 rendering, stock interrupts and unregister-on-destruction use the retail resource; sixteen sprites submit 96 screen vertices within the sidebar. Excludes full native HUD construction, pixel equivalence and physical GPU output.',sourceHashes:Object.fromEntries(sources.map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-hud-icons-native.py','tools/th14-hud-icons-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))};
writeFileSync(resolve(root,'docs/porting/th14-hud-icons-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${frames} native icon frames, sixteen registered icons, 96 render vertices and lifecycle cleanup.`);
