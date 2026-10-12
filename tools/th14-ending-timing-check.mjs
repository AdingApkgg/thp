import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/ending-timing-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-ending-timing-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-ending-timing-fixture.cpp',path=resolve(out,'ending-timing.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ending-timing-native.json'),'utf8'));
let inputFrames=0;
for(const row of proof.inputRows){c.input_init(row.initial);for(const sample of row.samples){const p=c.input_run(sample.held);assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,p,70)),[...sample.state,...sample.counts,...sample.heldFrames],`input initial ${row.initial}, frame ${inputFrames}`);++inputFrames;}}
for(const [i,row] of [...proof.rows,...proof.callbacks].entries()){
 const initialFlags=row.callback?row.flags:1;
 const p=c.run(row.op,row.duration,row.wait,row.seen,row.held,row.shootFrames,row.pressed,row.rate,row.time,initialFlags,row.frames??0,Number(!!row.callback));assert.notEqual(p,0,`run ${i}`);
 const got=Array.from(new Uint32Array(c.memory.buffer,p,row.callback?16:15)),expected=[Number(row.active),row.offset,row.flags,row.line,row.color,row.sounds.length,...row.timers.flat(),...(row.callback?[row.finalFrames]:[])];
 assert.deepEqual(got,expected,`native case ${i}: ${JSON.stringify(row)}`);assert.ok(row.sounds.every(n=>n===0));
 assert.equal(new Uint32Array(c.memory.buffer,p,17)[16],row.musicFadeFrames>>>0,`music fade ${i}: ${JSON.stringify(row)}`);
 const f=Array.from(new Uint32Array(c.memory.buffer,c.fade_words(),8));assert.equal(f[0],row.fades.length);
 if(row.fades.length){assert.equal(row.fades.length,1);const [type,duration,r,g,b,priority]=row.fades[0];assert.deepEqual([r,g,b],[0,0,0]);assert.deepEqual(f,[1,type,duration,0,priority,0xffffffff,0,0],`fade factory ${i}`);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-ending-timing-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,schedulerCases:proof.callbacks.length,inputFrames,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail420260/4202d0 including real Timer setters/advance/tick versus production Ending::update: wait opcodes5/6, future timed color9, slowdown-adjusted integer-second BGM fade11, fade creation13/14, all previous/current/fractional timer bits, instruction position, active/seen flags, line/color, sound/music-fade/fade descriptor requests. Retail41ff70 scheduler restarts versus Ending::tick, including staff/ordinary/first-view flags and unsigned frame wrap. Retail407540 versus GameInput repeat and continuous counters on four input streams including wrap. Sound/audio queue and fade factory delivery are controlled. Does not prove asynchronous resource loading, remaining opcodes, physical input delivery, audio output or GPU rendering.',sourceHashes:Object.fromEntries([fixture,'cpp/game/Ending.cpp','cpp/game/Ending.hpp','cpp/game/Timer.hpp','cpp/game/ScreenFade.hpp','cpp/game/GameSession.cpp','cpp/game/GameInput.cpp','cpp/game/GameInput.hpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th14-ending-timing-native.py','tools/th14-ending-timing-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} retail ending wait/timer cases, ${proof.callbacks.length} scheduler cases, ${inputFrames} input samples`);
