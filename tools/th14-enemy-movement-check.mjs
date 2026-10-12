import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-movement-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-enemy-movement-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['EnemyTh14Commands','EnemyState','EclContext','Movement','Interpolation'].map(n=>'cpp/game/'+n+'.cpp');sources.push('tests/cpp/th14-enemy-movement-fixture.cpp');const wasm=resolve(out,'movement.wasm');
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-enemy-movement-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-movement-native.json'),'utf8'));
const put=values=>{const size=Math.max(values.length,7),p=c.allocate(size*4),words=new Uint32Array(c.memory.buffer,p,size);words.fill(0);words.set(values);return p;};
const actual=()=>Array.from({length:53},(_,i)=>c.value(i)>>>0);
for(const row of proof.commands){const p=put(row.initial),a=put([...row.args,0]);try{c.initialize(p,1);assert.equal(c.command(row.op,a),0);assert.deepEqual(actual(),row.result,`command ${row.op} case ${row.n}`);}finally{c.release(p);c.release(a);}}
for(const row of proof.timelines){const p=put(row.initial);try{c.initialize(p,row.rate);for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,`timeline ${row.n} frame ${frame} status`);assert.deepEqual(actual(),expected.result,`timeline ${row.n} frame ${frame}`);}}finally{c.release(p);}}
const interp=()=>Array.from({length:4},(_,n)=>Array.from({length:11},(_,i)=>c.interpolation_value(n,i)>>>0));
for(const row of proof.interpolations){const p=put(row.initial),a=put([...row.args,0]),label=`interpolation ${row.op} case ${row.n} flags ${row.initial.at(-1)}`;try{
 c.initialize(p,row.rate);assert.equal(c.command(row.op,a),0,label);assert.deepEqual(actual(),row.configuredState,label+' configured state');assert.deepEqual(interp(),row.configured,label+' configured interpolation');
 for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,label+` frame ${frame} status`);assert.deepEqual(actual(),expected.result,label+` frame ${frame}`);assert.deepEqual(interp(),expected.interpolation,label+` frame ${frame} interpolation`);}
}finally{c.release(p);c.release(a);}}
const transcribed=proof.siblings;
for(const [n,row] of proof.randomRows.entries()){const p=put(row.initial),a=put([...row.args,0,0]),label=`random ${row.op} ${n}`;try{
 c.initialize(p,row.rate);c.random_setup(row.seed,row.player);assert.equal(c.command(row.op,a),0,label);assert.deepEqual(actual(),row.configuredState,label+' state');assert.deepEqual(interp(),row.configured,label+' bands');assert.deepEqual([c.random_value(0),c.random_value(1)],row.rng,label+' RNG');
 for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,label+` frame ${frame} status`);assert.deepEqual(actual(),expected.result,label+` frame ${frame}`);assert.deepEqual(interp(),expected.interpolation,label+` frame ${frame} bands`);}
}finally{c.release(p);c.release(a);}}
const positionBands=()=>Array.from({length:2},(_,n)=>Array.from({length:19},(_,k)=>c.position_value(n,k)>>>0));
for(const row of proof.positionRows){const p=put(row.initial),a=put([...row.args,0]),label=`position ${row.op} case ${row.n}`;try{
 c.initialize(p,row.rate);assert.equal(c.command(row.op,a),0,label);assert.deepEqual(actual(),row.configuredState,label+' configured state');assert.deepEqual(positionBands(),row.configured,label+' configured bands');
 for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,label+` frame ${frame} status`);assert.deepEqual(actual(),expected.result,label+` frame ${frame}`);assert.deepEqual(positionBands(),expected.bands,label+` frame ${frame} bands`);}
}finally{c.release(p);c.release(a);}}
for(const row of transcribed){const p=put(row.initial),a=put([...row.args,0]);try{c.initialize(p,1);assert.equal(c.command(row.op,a),0,`sibling ${row.op} case ${row.n}`);assert.deepEqual(actual(),row.result,`sibling ${row.op} case ${row.n} state`);}finally{c.release(p);c.release(a);}}
for(const row of proof.modeTimelines){const p=put(row.initial);try{c.initialize(p,row.rate);for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,`mode ${row.n} frame ${frame} status`);assert.deepEqual(actual(),expected.result,`mode ${row.n} frame ${frame}`);}}finally{c.release(p);}}
for(const row of proof.modeTimelinesExtra){const p=put(row.initial);try{c.initialize(p,row.rate);for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,`ellipse ${row.n} frame ${frame} status`);assert.deepEqual(actual(),expected.result,`ellipse ${row.n} frame ${frame}`);}}finally{c.release(p);}}
for(const row of proof.bandSets){const p=put(row.initial),a=put([...row.args,0]),label=`band ${row.op} case ${row.n}`;try{c.initialize(p,row.rate);assert.equal(c.command(row.op,a),0,label);assert.deepEqual(actual(),row.configuredState,label+' configured state');assert.deepEqual(interp(),row.configured,label+' configured bands');}finally{c.release(p);c.release(a);}}
for(const row of proof.slotRows){const p=put(row.initial),a=put([...row.args,0]),label=`slot ${row.op} case ${row.n}`;try{c.initialize(p,1);assert.equal(c.state_command(row.op,a,row.args.length),0,label);assert.deepEqual(actual(),row.result,label+' state');assert.deepEqual(proof.slotFields.map(([s,f])=>c.slot_value(s,f)>>>0),row.values,label+' slot words');}finally{c.release(p);c.release(a);}}
let caseRows=0,caseWords=0;
for(const row of proof.caseRows){const p=put(row.initial),a=put(row.args),label=`case ${row.op} row ${row.n} index ${row.index}`,slots=c.offset_of(0);try{
 c.initialize(p,1);c.seed(slots+row.index*0x380,put(row.before),2);c.seed(slots+row.index*0x380+8,put(row.record),row.record.length);
 c.seed(c.offset_of(2),put(row.vectors.slice(0,48)),48);c.seed(c.offset_of(3),put(row.vectors.slice(48)),48);
 // All four production consumers now require a real LaserManager. This
 // request-only fixture deliberately has none; compare the constructed
 // bytes, and retain the explicit unavailable-consumer diagnostic.
 assert.equal(c.state_command(row.op,a,row.op===713||row.op===703?2:1),-2,label+' missing laser manager');assert.deepEqual(actual(),row.result,label+' state');
 assert.deepEqual(Array.from({length:row.request.length},(_,n)=>c.request_word(n)>>>0),row.request,label+' request');
 caseRows+=1;caseWords+=row.request.length;
}finally{c.release(p);c.release(a);}}
let fireRows=0,fireWords=0;
for(const row of proof.fireRows){const p=put(row.initial),label=`op 601 row ${row.n} index ${row.index}`,slots=c.offset_of(0);try{
 c.initialize(p,1);c.seed(slots+row.index*0x380,put(row.record),row.record.length);
 c.seed(c.offset_of(2),put(row.vectors.slice(0,48)),48);c.seed(c.offset_of(3),put(row.vectors.slice(48)),48);
 c.fire_head(row.index);
 assert.deepEqual(Array.from({length:0x380/4},(_,n)=>c.record_word(row.index,n)>>>0),row.head,label);
 fireRows+=1;fireWords+=0x380/4;
}finally{c.release(p);}}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,commands:proof.commands.length,laserRequestRows:caseRows,laserRequestWords:caseWords,op601Rows:fireRows,op601Words:fireWords,
timelines:proof.timelines.length,frames:proof.timelines.reduce((n,r)=>n+r.frames.length,0),interpolationTimelines:proof.interpolations.length,interpolationFrames:proof.interpolations.reduce((n,r)=>n+r.frames.length,0),modeFrames:proof.modeTimelines.reduce((n,r)=>n+r.frames.length,0),modeExtraFrames:proof.modeTimelinesExtra.reduce((n,r)=>n+r.frames.length,0),bandSets:proof.bandSets.length,slotRows:proof.slotRows.length,slotValues:proof.slotRows.length*proof.slotFields.length,constantVelocityRecords:transcribed.length,siblingRecordsObserved:proof.siblings.length,siblingCounts:{409:proof.siblings.filter(r=>r.op===409).length,410:proof.siblings.filter(r=>r.op===410).length,411:proof.siblings.filter(r=>r.op===411).length,408:proof.siblings.filter(r=>r.op===408).length},case702Rows:proof.caseRows.filter(r=>r.op===702).length,case702Words:proof.caseRows.filter(r=>r.op===702).length*0x354/4,case702Spawner:proof.spawner,nativeExecutableSha256:proof.executableSha256,
 scope:'Actual retail TH14 setter dispatch and complete 4230d0 movement. Compares four movement records, flags, four scalar interpolation bands, two Vec3 position bands and their clocks. Includes 400/402 position, 404/406/428/430 angle/speed, 416/417 displacement, 424 mirror; scalar angle/speed interpolation, constant-velocity and selected circular/ellipse movement, camera displacement, clamp and visibility. Scalar 409/411 request setup is included here; full paired radius consumption has its separate orbit report. ANM lookup and argument getters are controlled. 700/701 slot writes and 601 emission position/descriptor are checked. 702/703/711/713 native factories are recorded boundaries; the canonical fixture deliberately lacks LaserManager and returns -2 after constructing the byte-identical request. Actual laser consumers have separate reports. Mode 4 is additionally checked with zero initial phase/anchor; separately seeded fields and interpolator interaction are covered by the wave report. Separate angle/ellipse interpolation bands remain outside this check.',
 wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EnemyState.hpp','cpp/game/EnemyScript.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
report.case713Rows=proof.caseRows.filter(r=>r.op===713).length;report.scope+=' ECL 713 kind-3 request at 428e6a is checked byte-for-byte, including explicit object id argument and its distinct 0x3c body offset.';
report.case711Rows=proof.caseRows.filter(r=>r.op===711).length;report.scope+=' ECL 711 request setup at 429014 is additionally checked, with missing downstream manager explicitly rejected by the fixture; the real kind-2 consumer is covered by separate curve-laser reports.';
report.hermitePositionTimelines=proof.positionRows.filter(r=>r.op===425||r.op===426||r.op===427).length;report.scope+=' Also checks ECL 425/426/427 Hermite position setup, tangent pairs and selected negative/zero/positive durations through actual 4261c6 and 4230d0.';
report.positionInterpolationTimelines=proof.positionRows.length;report.positionInterpolationFrames=proof.positionRows.reduce((n,r)=>n+r.frames.length,0);
report.ellipseModeFrames=proof.modeTimelinesExtra.reduce((n,r)=>n+r.frames.length,0);report.scope+=' 420/422 six-argument ellipse setters and mode-3/4 movement frames are additionally verified.';
report.case703Rows=proof.caseRows.filter(r=>r.op===703).length;report.case703Words=report.case703Rows*0x374/4;report.scope+=' ECL 703 copies the full 0x374-byte kind-1 request to native 43a750, including warning/expansion/active/shrink durations, sounds, sprite/color, position/offset, angular velocity and transform body. This proof covers request construction; the kind-1 consumer has its separate laser-infinite report.';
report.randomMovementTimelines=proof.randomRows.length;report.randomMovementFrames=proof.randomRows.reduce((n,r)=>n+r.frames.length,0);report.scope+=' ECL 412/413 random-direction setup and selected mode 0/4/7/17/18..31 and -1/80 default frame timelines include shared RNG seed/calls, player-side and clamp-quarter tests; speed interpolation mode retention follows the retail store.';
report.scope+=' Also verifies 401/403 Vec3 position interpolation in modes 0..31 and -1/80 defaults, sentinel endpoints, completion and resumed velocity, plus 440/442 angle, 444/446 speed, 441/443 angle interpolation. Modes 18..31 now use the original sine/reverse-parabola easing table through the complete enemy movement path; angle/speed interpolation also covers -1/80 defaults.';
writeFileSync(resolve(root,'docs/porting/th14-enemy-movement-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.commands} setters, ${report.frames} linear frames, ${report.interpolationTimelines} scalar timelines / ${report.interpolationFrames} frames, ${report.positionInterpolationTimelines} position timelines / ${report.positionInterpolationFrames} frames, ${report.modeFrames} mode-table frames, ${report.bandSets} band sets, ${report.slotRows} slot rows / ${report.slotValues} slot words, ${report.laserRequestRows} laser requests / ${report.laserRequestWords} request words, ${report.op601Rows} op-601 records / ${report.op601Words} record words, ${report.constantVelocityRecords} constant-velocity records.`);
