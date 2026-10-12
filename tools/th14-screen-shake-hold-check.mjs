import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/screen-shake-hold-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-screen-shake-hold-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-screen-shake-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'shake.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/screen-shake-hold-native.json'),'utf8'));
for(const [index,r] of proof.rows.entries()){
 assert.equal(c.begin_hold(...r.args),0,`constructor ${index}`);
 for(const [frame,row] of r.frames.entries()){c.tick(r.stopped);assert.deepEqual(Array.from({length:8},(_,n)=>c.value(n)>>>0),row,`frame ${index}/${frame}`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/ScreenShake.cpp','cpp/game/ScreenShake.hpp','cpp/game/Timer.hpp','cpp/game/Rng.hpp','cpp/game/GameBattle.cpp'];
const report={passed:true,cases:proof.rows.length,frames:proof.rows.reduce((n,r)=>n+r.frames.length,0),nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Full native 46cf60 phased shake update and actual timer/visual RNG. Production start_th14_hold/update compared for rise/hold/fall, zero rise/hold, signed amplitude, five clock rates, three seeds, stopped state, raw camera offsets and visual RNG seed/call count through removal. Active stage flags are controlled to zero; constructor/callback allocation and scaled render offsets are separate. Does not prove multi-effect callback ordering or GPU pixels.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-screen-shake-hold-native.py','tools/th14-screen-shake-hold-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-screen-shake-hold-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} phased shake timelines / ${report.frames} native frames.`);
