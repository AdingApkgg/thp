import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/pause-entry-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-pause-update-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'pause-entry.wasm'),fixture='tests/cpp/th16-pause-entry-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/pause-update-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.update_case(r.kind,r.sub,r.clock,r.replay,r.continues,r.rate,r.selected,r.pressed,r.repeat),1,JSON.stringify({index,...r}));
 assert.deepEqual(Array.from({length:68},(_,n)=>c.update_word(n)>>>0),r.output,JSON.stringify({index,...r}));assert.deepEqual(Array.from({length:c.sound_count()},(_,n)=>c.sound(n)),r.sounds);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-pause-update-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own43e5f0 complete wrapper and selected43f980 branches: substate0/1 initialization, game-over2-5 before score/name transition, navigation/escape, choices0/1/4 and shortcuts in6, confirmation7/9, return8, exits0/1/4 in16. Real418720/440c00 selection,402de0/402e20 history and both clock bodies execute. Repeat predicate, absent ANM children, handle interrupts/release, audio, logging and resume delivery are controlled. Compare cursor/history, disabled rows, substate, clocks, root/capture labels, sounds and host actions. Score/name, saving after substate10, manual and full session consumers excluded.',sourceHashes:Object.fromEntries(['cpp/game/PauseMenu.cpp','cpp/game/PauseMenu.hpp','cpp/game/PauseEnd.cpp','cpp/game/MenuCursor.cpp','cpp/game/MenuCursor.hpp','cpp/game/AnmManager.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 pause update cases`);
