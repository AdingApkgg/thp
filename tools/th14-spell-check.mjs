import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/spell-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-spell-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'spell.wasm'),sources=['cpp/game/SpellController.cpp','cpp/game/SpellController.hpp','cpp/game/SpellTh14Visuals.cpp','cpp/game/SpellTh14Visuals.hpp','tests/cpp/th14-spell-fixture.cpp'];
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',...['allocate','release','begin','update','end','end_command','factory','command','value','count'].map(n=>'-Wl,--export='+n),'-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','tests/cpp/th14-spell-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-native.json'),'utf8'));
const values=g=>Array.from({length:c.count(g)},(_,n)=>c.value(g,n)>>>0),check=(kind,rows,fn)=>{for(const [n,row] of rows.entries()){const p=c.allocate(row.input.length*4);try{new Uint32Array(c.memory.buffer,p,row.input.length).set(row.input);assert.equal(c[kind](p),1,`${kind} ${n}`);fn(row,n);}finally{c.release(p);}}};
check('begin',proof.begins,(r,n)=>{assert.deepEqual(values(0),r.state,`begin state ${n}`);assert.deepEqual(values(1),r.records,`begin records ${n}`);assert.deepEqual(values(4),r.timers,`begin timers ${n}`);});
check('factory',proof.factories,(r,n)=>{assert.deepEqual(values(0),r.created.flat(),`factory ${n}`);assert.deepEqual(values(1),r.childTimeouts,`factory child timers ${n}`);assert.deepEqual(values(2),r.sounds,`factory sounds ${n}`);});
check('update',proof.updates,(r,n)=>{assert.deepEqual(values(0),r.state,`update state ${n}`);assert.deepEqual(values(1),[r.background,...r.circle],`update visual targets ${n}`);assert.deepEqual(values(3),r.titles,`update titles ${n}`);});
check('end',proof.ends,(r,n)=>{assert.deepEqual(values(0),[r.flags,r.score,r.background],`end state ${n}`);assert.deepEqual(values(1),r.records,`end records ${n}`);for(const [g,v] of [[2,r.sounds],[3,r.titles],[4,r.timers],[5,r.closed],[6,r.results.flat().map(Number)]])assert.deepEqual(values(g),v,`end effects ${n}, group ${g}`);});
for(const [n,r] of proof.commands.entries()){const p=c.allocate(r.raw.length);try{new Uint8Array(c.memory.buffer,p,r.raw.length).set(r.raw);assert.equal(c.command(p,r.raw.length,r.difficulty,r.health,r.flags,r.timerMode),0,`ECL ${n}`);assert.deepEqual(values(0),r.state,`ECL state ${n}`);assert.deepEqual(values(6),r.call.slice(0,2),`ECL arguments ${n}`);assert.deepEqual(values(5),r.call[5],`ECL name ${n}`);assert.deepEqual(r.reads,[0,2,1]);}finally{c.release(p);}}
for(const [n,r] of proof.ends.entries()){
 const p=c.allocate(r.input.length*4);try{new Uint32Array(c.memory.buffer,p,r.input.length).set(r.input);assert.equal(c.end_command(p,r.healthFlags),0,`523 ${n}`);
 assert.deepEqual(values(0),[r.flags,r.score,r.background,r.endHealthFlags],`523 state ${n}`);assert.deepEqual(values(1),r.records,`523 records ${n}`);
 for(const [g,v] of [[2,r.sounds],[3,r.titles],[4,r.timers],[5,r.closed],[6,r.results.flat().map(Number)]])assert.deepEqual(values(g),v,`523 effects ${n}, group ${g}`);
 }finally{c.release(p);}
}
sources.push('cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyManager.cpp','cpp/game/EnemyScript.cpp');
for(const r of proof.orientations)assert.equal(c.orientation(r.flags,r.value)>>>0,r.result,JSON.stringify(r));
for(const r of proof.invalidations)assert.equal(c.invalidate(r.flags)>>>0,r.result,JSON.stringify(r));
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,beginCases:proof.begins.length,visualFactoryCases:proof.factories.length,updateCases:proof.updates.length,endCases:proof.ends.length,endEclCases:proof.ends.length,eclCases:proof.commands.length,nativeExecutableSha256:proof.executableSha256,scope:'Retail 41cb70, 41c5b0 and 41d450 state, normal/practice attempt/capture counters, wrapping/clamped score, survival decay, timers, inverted title thresholds, circle smoothing and requests to controlled ANM/title/timer/result/audio boundaries. Visual factory resource slots, scripts, stage/section/id background selection, root positions/rotation/flag 200, sound 33 and circle child timeouts are compared with controlled retail ANM first-update and synthetic port scripts. ECL 522/537/538/539 encrypted names, difficulty id adjustment, duration and health/timer setup are compared at a controlled begin call. ECL 523 production dispatch is compared with actual 4289ea -> 41d450, including inactive/active paths and clearing the owner health flag after end. Result HUD delivery is proved separately in th14-hud-notice-verified.json. No actual ANM resource, font, audio, score.dat or complete spell gameplay equivalence claim.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
report.captureInvalidationCases=proof.invalidations.length;report.scope+=' ECL 542 real dispatch replaces spell flags with flags OR 8, compared at 4289fb.';
report.titleOrientationCases=proof.orientations.length;report.scope+=' ECL 567 passes its integer to the retail 421c90 replacement of spell flag bit 8; inverted title thresholds are covered by the update cases.';
writeFileSync(resolve(root,'docs/porting/th14-spell-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.beginCases} begin, ${report.updateCases} update, ${report.endCases} end cases.`);
