import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/reimu-orb-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-reimu-orb-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-reimu-orb-fixture.cpp',sources=['cpp/game/BombReimuTh14.cpp','cpp/game/Movement.cpp'],wasm=resolve(out,'orb.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...sources,'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/reimu-orb-native.json'),'utf8'));
const setup=r=>{const p=c.allocate(r.words.length*4);new Uint32Array(c.memory.buffer,p,r.words.length).set(r.words);c.setup(p,r.target??0,r.present??1,r.flags??0,...(r.position??[0,100]),r.rate,r.index);};
const state=()=>Array.from({length:18},(_,i)=>c.value(i)>>>0);
for(const r of proof.cases){setup(r);c.tick();assert.deepEqual(state(),r.result,JSON.stringify(r));}
for(const p of proof.paths){setup(p);for(const [frame,result] of p.result.entries()){c.tick();assert.deepEqual(state(),result,`path index=${p.index} rate=${p.rate} frame=${frame}`);}}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-reimu-orb-verified.json'),JSON.stringify({passed:true,isolatedFrames:proof.cases.length,paths:proof.paths.length,sequentialFrames:proof.paths.reduce((n,p)=>n+p.result.length,0),nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 414510 orb motion including 42c310 nearest-target selection, target flags, orbit radius/anchor/angular rate, staggered detachment, atan2/sqrt, steering speed clamps, out-of-bounds slowing, native 403cd0/403df0 movement, retained linear z, hundredth-pixel floor, delta history and rate-sensitive clock. Only ANM lookup is controlled. Bomb controller, area ownership, damage, cancellation, allocation failure and GPU rendering are separate.',sourceHashes:Object.fromEntries([fixture,...sources,'cpp/game/BombReimuTh14.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-reimu-orb-native.py','tools/th14-reimu-orb-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS: ${proof.cases.length} isolated frames, ${proof.paths.length} paths.`);
