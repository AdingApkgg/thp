import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/player-lifecycle-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-player-lifecycle-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'lifecycle.wasm'),fixture='tests/cpp/th14-player-lifecycle-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/player-lifecycle-native.json'),'utf8'));
const buffer=new ArrayBuffer(4),u=new Uint32Array(buffer),f=new Float32Array(buffer);const float=n=>{u[0]=n;return f[0];};
const trunc=n=>!Number.isFinite(n)||n>=2147483648||n< -2147483648? -2147483648:Math.trunc(n);
for(const r of proof.rows){
 assert.equal(c.run(...r.args),1,`run failed ${c.error()} ${JSON.stringify(r.args)}`);
 const expected=r.result.slice(),kind=r.args[0];
 // Retail comparison stops at 44dfd1, before the independently verified
 // common ANM/scale tail. Production update also advances the two clocks.
 if(kind!==5&&kind!==6){const speed=float(expected[19]);expected[1]=(speed>.99&&speed<1.01?expected[1]+1:trunc(Math.fround(Math.fround(expected[1]|0)+speed)))>>>0;
  if((expected[2]|0)>0)expected[2]=trunc(Math.fround(Math.fround(expected[2]|0)-(speed>.99&&speed<1.01?1:speed)))>>>0;}
 assert.deepEqual(Array.from({length:21},(_,n)=>c.value(n)>>>0),expected,JSON.stringify(r.args));
 const events=Array.from({length:c.event_count()},(_,n)=>Array.from({length:c.event_size(n)},(_,j)=>c.event_value(n,j)>>>0));
 assert.deepEqual(events,r.events,`events ${JSON.stringify(r.args)}`);
 assert.equal(c.value(20),5000000,'TH14 death preserves point-item value');assert.equal(c.value(21),1000,'TH14 death preserves legacy rank storage');
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Retail 44f7a0 hit, 44f5e0 death and 44dbd0..44dfd1 lifecycle dispatch compared to production PlayerFrame hit/die/update using original player/effect ANM resources. Checks effect script 28/27, sound 2 suppression, spell failure, lives, stock-only Bomb consumption via actual retail 412110, eight-frame deathbomb boundary, 30-frame loss/respawn, preserved fragments, 3-Bomb refill, 60-frame entry, fixed-point Y, exact SSE laser radii and circle/all cancellation arguments. Native movement, ANM, HUD, bullet/laser managers, death damage-area allocation and Bomb vtable effects are controlled boundaries; production runs real ANM while comparisons exclude their internal state. Native comparison stops before common update tail and accounts for production clock advancement. Excludes full Bomb behavior, GPU pixels, audio playback, replay and all-title equivalence.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerFrame.cpp','cpp/game/PlayerFrame.hpp','cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp','cpp/game/BombController.cpp','cpp/game/GameEconomy.hpp','cpp/game/Timer.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-player-lifecycle-native.py','tools/th14-player-lifecycle-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-player-lifecycle-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail player lifecycle cases with original ANM resources.`);
