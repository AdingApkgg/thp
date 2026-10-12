import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-season-drop-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-enemy-season-drop-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'enemy-season-drop.wasm'),fixture='tests/cpp/th16-enemy-season-drop-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-season-drop-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.run_case(r.step,r.next,r.total,r.seed,r.calls,...r.position),1);
 assert.deepEqual(Array.from({length:3},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify({index,...r}));
 assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>c.event(n)>>>0),r.events.flat(),JSON.stringify({index,...r}));
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-enemy-season-drop-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own41c72f..41c7a6 damage seasonal drop body and complete native402c70/402cf0 RNG. Compare threshold increments, signed guards, current position, type16, angle, speed, force0, RNG seed and wrapping draw count.430960 is a recorded factory boundary, independently compared by th16-item-factory-verified.json. Signed threshold overflow is rejected rather than reproducing a potentially infinite native loop; full enemy frame, item update, renderer and campaign remain excluded.',sourceHashes:Object.fromEntries(['cpp/game/EnemyTh16Commands.cpp','cpp/game/EnemyCommands.hpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyFrame.hpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 damage seasonal drop sequences`);
