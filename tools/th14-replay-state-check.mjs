import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/replay-state-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-replay-state-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'replay-state.wasm'),fixture='tests/cpp/th14-replay-state-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/replay-state-native.json'),'utf8'));
for(const r of proof.cases)for(const first of [0]){const h=Buffer.from(r.header,'hex'),p=c.allocate(h.length);new Uint8Array(c.memory.buffer,p,h.length).set(h);c.restore_snapshot(p,r.visualCalls,first);c.release(p);const g=r.globals;
 const expected=[...r.rng,...[2,12,9,6,8,11,13,14,15,16,17,18,19,27,20,22,23,24,25,26].map(n=>g[n]),h.readUInt32LE(12),h.readUInt32LE(16),g[4],g[7],h.readUInt32LE(0x84),...g,...Array.from({length:20},(_,n)=>h.readUInt32LE(0x88+n*4))];
 assert.deepEqual(Array.from({length:expected.length},(_,n)=>c.snapshot_word(n)>>>0),expected,r.name);
}
for(const r of proof.routes){
 const h=Buffer.from(r.header,'hex'),p=c.allocate(h.length);new Uint8Array(c.memory.buffer,p,h.length).set(h);
 c.restore_snapshot(p,r.visualCalls,Number(r.first));c.release(p);
 assert.deepEqual([c.snapshot_word(1)>>>0,c.snapshot_word(3)>>>0],r.visual,`entry flags ${r.flags} calls ${r.visualCalls}`);
}
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
for(let demo=0;demo<3;demo++){
 let seed,calls;
 for(const incoming of [0,97,0x80000000,0xffffffff]){
  assert.equal(c.begin_counted_demo(demo,incoming),1);
  if(incoming===0){seed=c.visual_word(0)>>>0;calls=c.visual_word(1)>>>0;}
  assert.equal(c.visual_word(0)>>>0,seed,`demo${demo} seed`);
  assert.equal(c.visual_word(1)>>>0,(calls+incoming)>>>0,`demo${demo} preserves prior visual calls ${incoming}`);
 }
}
for(const r of proof.power){assert.equal(c.initialize_power(r.selection,r.rawStep),1);assert.deepEqual(Array.from({length:3},(_,n)=>c.power_word(n)>>>0),r.output);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-replay-state-verified.json'),JSON.stringify({passed:true,completeGame:false,snapshots:proof.cases.length,productionRestores:proof.cases.length,initialRoutes:proof.routes.length,originalDemoEntries:12,livePowerSteps:proof.power.length,nativeExecutableSha256:proof.executableSha256,scope:'Whole456050 playback-mode stage restore executes without hooks: all28 snapshot words and both RNG seeds, gameplay call reset and preserved visual call count across four unsigned counter values; production existing-controller restores, seven-stage indexing subset1/3/7, seed0/1/9630/ffff and 96 synthetic plus3 shipped replay headers with four visual-call counters each. Portable ReplayStageState mapped economy fields, unnamed snapshot preservation, position, weapon and spell times compared. Native44c600..44c628 power-step stores compared with actual production PlayerFrame initialization using all6 real SHT/ANM loadouts and raw steps40/80/100/200. 435ed0..435f50 initial/transition routing compared for 32 flags/counter combinations: first construction preserves visual seed/count; existing-controller routing runs actual456050. Resource construction is a controlled boundary for this local route. Twelve production original-asset demo entries also preserve incoming visual counts modulo 2^32 with unchanged seeded ANM initialization. Full replay-manager lifecycle, later game/RNG call order, native recorder/save, pixels and complete game excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/Replay.cpp','cpp/game/Replay.hpp','cpp/game/GameSession.cpp','cpp/game/Rng.hpp','cpp/game/PlayerFrame.cpp',fixture,'tests/cpp/th14-replay-session-fixture.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} native snapshots / ${proof.cases.length} production next-stage restores / 12 original-asset demo entries / ${proof.power.length} power-step initializations`);
