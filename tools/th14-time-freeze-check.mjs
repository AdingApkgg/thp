import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/time-freeze-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th14-time-freeze-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-time-freeze-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'freeze.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/time-freeze-native.json'),'utf8'));
for(const r of [...proof.bullets,...proof.lasers]){
 assert.equal(c.begin(r.kind??0,r.flags??0,r.state,r.timer,r.rate),0,JSON.stringify(r));
 for(const [frame,f] of r.frames.entries()){
  const why=JSON.stringify({kind:r.kind,flags:r.flags,state:r.state,timer:r.timer,rate:r.rate,frame});assert.equal(c.tick(),1,why);
  assert.deepEqual(Array.from({length:f.result.length},(_,n)=>c.value(n)>>>0),f.result,why);
  assert.deepEqual(Array.from({length:c.event_words()},(_,n)=>c.event_value(n)>>>0),f.events.flat(),why+' delivery');assert.equal(c.graze(),f.graze,why+' graze');
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/BulletManager.hpp','cpp/game/BulletManager.cpp','cpp/game/BulletTh14.cpp','cpp/game/LaserManager.cpp','cpp/game/LaserState.hpp','cpp/game/LaserInfiniteTh14.cpp','cpp/game/LaserCurveTh14Runtime.cpp'];
const report={passed:true,bulletFrames:proof.bullets.length*5,laserFrames:proof.lasers.length*8,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail bullet manager and laser manager freeze dispatch versus production managers. Bullet state-1/state-2 lifetime threshold, flags, no movement/ANM/auxiliary advance when frozen, continued lifetime/group/count and single graze. Actual kind-1/kind-2 collision virtuals and inert kind-3, frozen lifetime, graze clocks and geometric request order. ANM delivery, player collision result and graze delivery are controlled. Kind-0 finite lasers and complete Bomb lifecycle are separate.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-time-freeze-native.py','tools/th14-time-freeze-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-time-freeze-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.bulletFrames} bullet and ${report.laserFrames} laser freeze frames.`);
