import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-movement-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-enemy-movement-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'movement.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16','tests/cpp/th16-enemy-movement-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-movement-native.json'),'utf8'));
const put=values=>{const p=c.allocate(Math.max(values.length,7)*4);new Uint32Array(c.memory.buffer,p,Math.max(values.length,7)).fill(0);new Uint32Array(c.memory.buffer,p,values.length).set(values);return p;};
const actual=()=>Array.from({length:53},(_,i)=>c.value(i)>>>0);
const interp=()=>Array.from({length:4},(_,n)=>Array.from({length:11},(_,i)=>c.interpolation_value(n,i)>>>0));
const bands=()=>Array.from({length:2},(_,n)=>Array.from({length:19},(_,i)=>c.position_value(n,i)>>>0));
for(const row of proof.commands){const p=put(row.initial),a=put(row.args);c.initialize(p,1);assert.equal(c.command(row.op,a),0);assert.deepEqual(actual(),row.result,`command ${row.op} / ${row.n}`);c.release(p);c.release(a);}
for(const row of [...proof.timelines,...proof.modeTimelines,...proof.modeTimelinesExtra].filter(r=>!r.initial.some((w,i)=>(i===38||i===51)&&(w&15)===4))){const p=put(row.initial);c.initialize(p,row.rate);for(const [f,v] of row.frames.entries()){assert.equal(c.tick()>>>0,v.status,`mode ${row.group}/${row.n}/${f}`);assert.deepEqual(actual(),v.result,`mode ${row.group}/${row.n}/${f}`);}c.release(p);}
for(const row of proof.interpolations){const p=put(row.initial),a=put(row.args),label=`scalar ${row.op}/${row.n}`;c.initialize(p,row.rate);assert.equal(c.command(row.op,a),0);assert.deepEqual(actual(),row.configuredState,label);assert.deepEqual(interp(),row.configured,label);for(const [f,v] of row.frames.entries()){assert.equal(c.tick()>>>0,v.status,label);assert.deepEqual(actual(),v.result,`${label}/${f}`);assert.deepEqual(interp(),v.interpolation,`${label}/${f}`);}c.release(p);c.release(a);}
for(const row of proof.positionRows){const p=put(row.initial),a=put(row.args),label=`position ${row.op}/${row.n}`;c.initialize(p,row.rate);assert.equal(c.command(row.op,a),0);assert.deepEqual(actual(),row.configuredState,label);assert.deepEqual(bands(),row.configured,label);for(const [f,v] of row.frames.entries()){assert.equal(c.tick()>>>0,v.status,label);assert.deepEqual(actual(),v.result,`${label}/${f}`);assert.deepEqual(bands(),v.bands,`${label}/${f}`);}c.release(p);c.release(a);}
for(const r of proof.directions){assert.equal(c.direction_case(r.flags,r.direction,r.velocityBits),+r.changed,JSON.stringify(r));if(r.changed)assert.deepEqual([c.direction_word(0)>>>0,c.direction_word(1)>>>0],r.result,JSON.stringify(r));}
for(const r of proof.marks){c.mark_case(...r.flags);assert.deepEqual(Array.from({length:5},(_,n)=>c.mark_word(n)>>>0),r.result,JSON.stringify(r));}
const paths=['cpp/game/EnemyTh16Movement.cpp','cpp/game/EnemyState.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyAnimations.cpp'];
const report={passed:true,title:16,completeGame:false,executableSha256:proof.executableSha256,commands:proof.commands.length,scalarTimelines:proof.interpolations.length,positionTimelines:proof.positionRows.length,directionRequests:proof.directions.length,retirementTrees:proof.marks.length,scope:'Own TH16 command entries and full 41bb50 movement consumer with ANM lookup returning zero. Modes 0..3, camera and clamp, four independent scalar bands and Vec3 bands. Additional41beee direction-request prefix and complete46f220 retirement marking over protected child branches. Mode4, actual direction animation factory/resource execution, child creation-mode consumer and full enemy frame excluded.',sources:Object.fromEntries(paths.map(p=>[p,createHash('sha256').update(readFileSync(resolve(rt,p))).digest('hex')]))};
writeFileSync(resolve(root,'docs/porting/th16-enemy-movement-verified.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS: TH16 movement',JSON.stringify(report));
