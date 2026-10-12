import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/player-death-drop-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-player-death-drop-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'drops.wasm'),fixture='tests/cpp/th14-player-death-drop-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/player-death-drop-native.json'),'utf8'));
for(const r of proof.cases){
 assert.equal(c.run(r.power,r.step,r.lives,...r.position),1);
 assert.equal(c.power()>>>0,r.result,JSON.stringify(r));
 assert.equal(c.count(),49);
 assert.deepEqual(Array.from({length:49},(_,n)=>c.value(n)>>>0),r.requests.flat(),JSON.stringify(r));
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,cases:proof.cases.length,itemRequests:proof.cases.length*7,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Actual retail 44dda3..44de99 death-frame-3 power subtraction, signed clamp, native 44ed80/4a753a angle calculation and seven ordinary type-1 drop requests. Varies signed power/step boundaries, lives, signed zeros, ordinary positions and large-Y zero delta. Item allocation and option reconstruction are controlled boundaries; unused native item argument is excluded. Verifies the helper called by PORT_TITLE=14 PlayerFrame::death_frame, not the full player lifecycle, respawn, item physics or option reconstruction.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerFrame.cpp','cpp/game/PlayerFrame.hpp','cpp/game/GameEconomy.hpp','cpp/game/GameBattle.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-player-death-drop-native.py','tools/th14-player-death-drop-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-player-death-drop-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} death-drop cases / ${report.itemRequests} native item requests.`);
