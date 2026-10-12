import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/music-fade-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-music-fade-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-music-fade-fixture.cpp',path=resolve(out,'music-fade.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',fixture,'cpp/game/SoundEffects.cpp','-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/music-fade-native.json'),'utf8'));let ticks=0;
for(const [n,row] of proof.rows.entries()){
 c.reset(row.frames,row.master);
 for(const [frame,s] of row.steps.entries()){
  assert.equal(c.tick(),s.result,`result ${n}/${frame}`);assert.deepEqual([0,1,2].map(i=>c.state(i)>>>0),s.state,`state ${n}/${frame}`);
  assert.deepEqual(c.event_count()?[[c.event_kind()===0?'stop':'volume',c.event_value()>>>0]]:[],s.events,`events ${n}/${frame}`);++ticks;
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-music-fade-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,timelines:proof.rows.length,ticks,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:proof.scope,sources:Object.fromEntries([fixture,'cpp/game/Th14MusicFade.hpp','cpp/game/SoundEffects.cpp','cpp/sdl/AudioDevice.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),tools:Object.fromEntries(['tools/th14-music-fade-native.py','tools/th14-music-fade-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} native fade timelines / ${ticks} ticks`);
