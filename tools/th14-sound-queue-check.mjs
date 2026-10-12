import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/sound-queue-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-sound-queue-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-sound-queue-fixture.cpp',path=resolve(out,'sound-queue.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,'cpp/game/SoundEffects.cpp','-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/sound-queue-native.json'),'utf8'));
const kinds=['indices','counts','pans','metadata'],state=()=>Object.fromEntries(kinds.map((k,i)=>[k,Array.from({length:i<2?12:i===2?1536:76},(_,n)=>c.state(i,n)>>>0)]));
for(const [n,r] of proof.rows.entries()){c.reset(100,1,1);for(const op of r.operations)c.operation(op[0]==='enqueue'?0:op[0]==='positioned'?1:2,op[1],op[0]==='enqueue'?op[2]:0,op[0]==='positioned'?op[2]:0);assert.deepEqual(state(),r.state,`queue${n}`);}
for(const [n,r] of proof.outputs.entries()){c.reset(r.master,r.enabled,r.present);c.operation(r.positioned?1:0,r.voice,0,96);if(r.stop)c.operation(2,r.voice,0,0);assert.deepEqual(state(),r.initial,`initial${n}`);c.process();assert.deepEqual(state(),r.state,`processed${n}`);
 const events=Array.from({length:c.event_count()},(_,i)=>Array.from({length:3},(_,k)=>c.event_value(i*3+k)>>>0));assert.deepEqual(events,r.events.map(([kind,id,value])=>[['stop','position','pan','volume','play'].indexOf(kind),id,value>>>0]),`events${n}`);
}
for(const [n,r] of proof.music.entries())assert.equal(c.music_volume(r.volume,r.master)>>>0,r.result,`music volume${n}`);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-sound-queue-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,queueCases:proof.rows.length,outputCases:proof.outputs.length,musicVolumeCases:proof.music.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:proof.scope,sources:Object.fromEntries([fixture,'cpp/game/SoundEffects.hpp','cpp/game/SoundEffects.cpp','cpp/game/Th14AudioTables.inc','cpp/sdl/AudioDevice.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),tools:Object.fromEntries(['tools/th14-sound-queue-native.py','tools/th14-sound-queue-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} original sound queues / ${proof.outputs.length} original sound outputs / ${proof.music.length} music volume cases`);
