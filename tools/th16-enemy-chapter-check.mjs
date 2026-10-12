import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-chapter-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-enemy-chapter-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'enemy-chapter.wasm'),fixture='tests/cpp/th16-enemy-chapter-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-chapter-native.json'),'utf8'));
for(const r of proof.erase){assert.equal(c.erase(r.flags),+r.selected);assert.deepEqual(Array.from({length:24},(_,n)=>c.erase_value(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.chapters){assert.equal(c.chapter(r.tag,r.credit),0);assert.deepEqual(Array.from({length:4},(_,n)=>c.chapter_value(n)>>>0),r.output,JSON.stringify(r));}
for(const r of proof.deaths){c.death(r.tag,r.chapter,r.credit);assert.deepEqual([c.death_value(0)>>>0,c.death_value(1)>>>0],r.output,JSON.stringify(r));}
for(const r of proof.credits){assert.equal(c.credit(r.tag,r.chapter,r.credit),0);assert.deepEqual([c.death_value(0)>>>0,c.death_value(1)>>>0],r.output,JSON.stringify(r));}
for(const r of proof.settings){assert.equal(c.setting(r.credit,r.value,r.spawned),0);assert.deepEqual([c.setting_value(0)>>>0,c.setting_value(1)>>>0],r.output,JSON.stringify(r));}
for(const r of proof.timers){assert.equal(c.timer_case(r.flags,r.rate),0);const words=()=>Array.from({length:5},(_,n)=>c.timer_word(n)>>>0);assert.deepEqual(words(),r.configured);for(const frame of r.frames){c.timer_tick();assert.deepEqual(words(),frame,JSON.stringify(r));}}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-enemy-chapter-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,eraseCases:proof.erase.length,chapterCases:proof.chapters.length,deathCreditCases:proof.deaths.length,ecl570Cases:proof.credits.length,nativeExecutableSha256:proof.executableSha256,scope:'Complete41d900 single-node erase preparation with death/memset boundaries: native protection mask,17 drop counts, spread, death reference, chapter credit and post-death flag. Native timer runs but is not compared here. Complete524 with argument sink and actual EnemyScriptServices routing, plus41d662 positive/current-chapter death-credit scalar and complete420410 ECL570 nonzero signed credits/current chapter/clear with actual EnemyScriptServices routing. Actual death, item factories, manager destruction, full enemy frame and gameplay excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/EnemyTh16Commands.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyState.cpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyCommands.hpp','cpp/game/Timer.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
const reportPath=resolve(root,'docs/porting/th16-enemy-chapter-verified.json'),report=JSON.parse(readFileSync(reportPath,'utf8'));
report.phaseTimerTimelines=proof.timers.length;report.phaseTimerFrames=proof.timers.reduce((n,r)=>n+r.frames.length,0);report.scope+=' Own ECL513 phase-clock reset and406190 ticks:24 timelines /960 frames; actual EnemyScriptServices routing. Native timer index0 is relocated to the production rate pointer.';report.sourceHashes['cpp/game/EnemyManager.cpp']=sha(readFileSync(resolve(rt,'cpp/game/EnemyManager.cpp')));
report.ecl569Cases=proof.settings.length;report.scope+=' Complete4203ba ECL569 credit setter: old zero positive-only spawn addition, old one signed replacement/adjustment, other credits unchanged; signed wrapping and actual EnemyScriptServices route.';
writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(`PASS ${proof.erase.length} erase preparations, ${proof.chapters.length} chapters, ${proof.deaths.length} death credits and ${proof.timers.length} phase-clock timelines`);
