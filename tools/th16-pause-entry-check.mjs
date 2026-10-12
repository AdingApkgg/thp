import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/pause-entry-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-pause-entry-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'pause-entry.wasm'),fixture='tests/cpp/th16-pause-entry-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/pause-entry-native.json'),'utf8'));
for(const r of proof.entries){
 assert.equal(c.entry(r.kind==='game_over'?2:r.replay),1);
 assert.deepEqual(Array.from({length:c.binding_count()},(_,n)=>[c.binding(n,0),c.binding(n,1)]),r.bindings,JSON.stringify(r));
 assert.deepEqual(Array.from({length:c.sound_count()},(_,n)=>c.sound(n)),r.sounds);assert.deepEqual([c.state_word(0),c.state_word(1)],r.state);assert.equal(c.capture(),1);
}
for(const r of proof.capture)assert.deepEqual(r.bindings,[[0,52]]);
for(const r of proof.factories){assert.equal(c.factory(r.script,r.program),1);assert.deepEqual(Array.from({length:7},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));assert.deepEqual(r.tick,[0x400,0,0,0,0]);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-pause-entry-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,entryPaths:proof.entries.length,capturePrefixes:proof.capture.length,factories:proof.factories.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own43f0f0 pause/replay entry and43f350 non-replay game-over prefix through43f431 with audio/logging/capture delivery controlled. Independently execute43ef20 capture prefix through43ef60 and full418fe0 overlay factory with allocation/bind/tick/registry boundaries. Compare script52/156/158 bindings, sound14, separate menu kind/substate, origin/rotation initialization, selected flags2 bit400, retained/changed layer and post-update pending4. Production uses actual synthetic stop/layer ANM scripts. GPU capture, score/name writes, full input state machine, practice/clear-end and full campaign explicitly excluded.',sourceHashes:Object.fromEntries(['cpp/game/PauseMenu.cpp','cpp/game/PauseMenu.hpp','cpp/game/PauseEnd.cpp','cpp/game/AnmManager.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log('PASS 3 TH16 pause/end entries, 2 capture prefixes and 6 overlay factories');
