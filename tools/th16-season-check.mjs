import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/season-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-season-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'season.wasm'),fixture='tests/cpp/th16-season-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/season-native.json'),'utf8'));
for(const r of proof.collection){assert.equal(c.collect(r.count,r.maximum),r.result,JSON.stringify(r));assert.equal(c.count()>>>0,r.output,JSON.stringify(r));assert.equal(c.progress()>>>0,r.progress,JSON.stringify(r));}
for(const r of proof.gauges){assert.equal(c.gauge(r.count,r.maximum,r.active,r.flags),1);assert.deepEqual(Array.from({length:8},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>c.event(n)>>>0),r.events.flat(),JSON.stringify(r));}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const r of proof.rewards){c.reward(r.kind,r.point,r.maximum,r.energy);assert.deepEqual(Array.from({length:3},(_,n)=>c.reward_word(n)>>>0),r.output,JSON.stringify(r));}
writeFileSync(resolve(root,'docs/porting/th16-season-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,collections:proof.collection.length,gauges:proof.gauges.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Complete43de50 count/level transitions and43df20 SSE progress. Complete42c600 after root/child resolver boundaries, including actual46f380/46f3b0 visibility helpers, bar width, active status, interrupts and immediate bar tick request. VM callback selectors zero and tick controlled; real root creation, ANM rendering, score extends, seasonal satellites/release and gameplay remain excluded.',sourceHashes:Object.fromEntries(['cpp/game/SeasonTh16.cpp','cpp/game/SeasonTh16.hpp','cpp/game/GameEconomy.hpp','cpp/game/Hud.cpp','cpp/game/Hud.hpp','cpp/game/GameBattle.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.collection.length} own TH16 season collections and ${proof.gauges.length} gauges`);
const reportPath=resolve(root,'docs/porting/th16-season-verified.json'),report=JSON.parse(readFileSync(reportPath,'utf8'));report.cancelRewards=proof.rewards.length;report.scope+=' Own42fe0d-42fe56 types9-14 reward request with complete430dc0/42c860, signed point value cap and wrapping, SSE release energy and score request. Full score/extend side effects remain excluded.';writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(`PASS ${proof.rewards.length} own TH16 special-item rewards`);
