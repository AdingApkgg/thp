import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/sakuya-a-controller-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-sakuya-a-controller-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-sakuya-b-controller-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'controller.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/sakuya-a-controller-native.json'),'utf8'));
const events=()=>Array.from({length:c.event_count()},(_,i)=>Array.from({length:c.event_size(i)},(_,k)=>c.event(i,k)>>>0));
for(const r of proof.start){const why=JSON.stringify(r);assert.equal(c.start_selection(4,r.flags,r.time),0,why);assert.deepEqual([...[0,1,2,3].map(n=>c.value(n)>>>0),c.player_flags()],r.result,why);assert.deepEqual(events(),[[1,44,1],[1,50,0]],why);assert.equal(c.created(),2,why);assert.deepEqual(Array.from({length:2},(_,i)=>['animation',c.script(i),...[0,1,2].map(a=>c.position(i,a)>>>0)]),r.events.filter(e=>e[0]==='animation'),why);}
const kinds={sound:1,cancel:3,item:5};
for(const r of proof.ticks){const why=JSON.stringify(r.args);assert.equal(c.tick_sakuya_a(...r.args),1,why);assert.deepEqual(Array.from({length:16},(_,n)=>c.sakuya_a_value(n)>>>0),r.result,why);assert.deepEqual(events(),r.events.filter(e=>e[0]!=='animation').map(e=>[kinds[e[0]],...e.slice(1)]),why);}
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=[fixture,'cpp/game/BombController.cpp','cpp/game/BombController.hpp','cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp','cpp/game/PlayerFrame.cpp','cpp/game/GameBattle.hpp','cpp/game/EnemyAnimations.cpp'];
const report={passed:true,startCases:proof.start.length,tickCases:proof.ticks.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual 415610 startup and 412200 common update through 415750/415a90, with controlled ANM lookup/factory, sound/item sinks and bullet/laser cancel delivery. Production selection 4 compared for spell fail, count, invincibility, script 16/19 requests, native player flag 8, active states 1/2, movement factor request, tracked position, scale decay, auxiliary age gate, hit-to-burst life/timer reset, interrupt 2, burst duration 60, missing main/auxiliary, frame 720/dialogue finish, three type-6 item positions and rates .5/1/1.25. Laser requests independently recorded natively and matched to bullet requests; production world callback represents the existing combined GameBattle delivery. Actual item rewards, moving player delta, ANM lifecycle/children, full firing and GPU pixels are separate.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-sakuya-a-controller-native.py','tools/th14-sakuya-a-controller-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-sakuya-a-controller-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.start.length} Sakuya A startup and ${proof.ticks.length} common update cases.`);
