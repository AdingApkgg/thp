import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-notice-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-hud-notice-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-hud-notice-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'notice.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-notice-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.begin(r.kind,r.value,r.mode),0,`case ${index}`);
 assert.deepEqual(Array.from({length:14},(_,n)=>c.slot_value(n)>>>0),r.slots,`slots ${index}`);
 assert.deepEqual(Array.from({length:39},(_,n)=>c.erased(n)),r.erased,`erase ${index}`);
 assert.equal(c.count(),r.created.length,`count ${index}`);
 for(const [n,row] of r.created.entries())assert.deepEqual(Array.from({length:9},(_,k)=>c.created_value(n,k)>>>0),row,`VM ${index}/${n}`);
}
assert.equal(c.icons_initialize(),0);
for(const [n,row] of proof.icons.entries())assert.deepEqual(Array.from({length:8},(_,k)=>c.icon_value(n,k)>>>0),row,`icon ${n}`);
for(const [index,r] of proof.displays.entries()){c.display_icons(r.count,r.fragments);assert.deepEqual(Array.from({length:16},(_,n)=>c.icon_pending(n)>>>0),r.pending,`display ${index}`);}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/Hud.hpp','cpp/game/Hud.cpp','cpp/game/HudTh14Notice.cpp','cpp/game/GameBattle.hpp','cpp/game/EnemyManager.cpp','cpp/game/GameEconomy.hpp'];
const report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 434430 notice types 0..6 including captured/failed spell results, signed bonus division and 1,000/1,000,000 separator thresholds, scripts, sprites, handle replacement, zero initial positions/rotation and flag 200 before first update. Actual 47f6e0/47f520/47f560 and inline deletion traverse root children only when child.previous is null. Tests cover missing handles, existing roots, two children, and non-parent chain members. Failure preserves earlier bonus VMs and neither result closes the old spell-time VM. Resource binding/tick, ANM registry allocation/lookup and sprite binding are controlled native boundaries; the port uses synthetic stop scripts and sprites. Actual resource animations, font rendering, HUD text layout and GPU pixels are unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
report.icons=proof.icons.length;report.displayCases=proof.displays.length;report.scope+=' Retail 42edf6..42efb5 life/Bomb icon initialization uses scripts 29..36/37..44, zero positions/rotation and flag 200. Retail 434ef0/434fd0 display interrupts are compared for 54 signed count/fragment inputs, including wrapping fragment multiplication and 16-bit partial labels. Allocation, resource binding and first update remain controlled boundaries.';
writeFileSync(resolve(root,'docs/porting/th14-hud-notice-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail HUD notice cases, ${report.icons} icons, ${report.displayCases} display cases.`);
