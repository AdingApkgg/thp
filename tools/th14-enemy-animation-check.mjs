import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-animation-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-enemy-animation-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'animations.wasm');
const fixture='tests/cpp/th14-enemy-animation-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-animation-native.json'),'utf8'));
for(const r of proof.offsets){assert.equal(c.offset_case(r.slot,r.x,r.y),0);assert.deepEqual(Array.from({length:48},(_,n)=>c.offset_word(n)>>>0),r.result,JSON.stringify(r));assert.deepEqual(r.reads,[0,1,2]);}
assert.equal(c.offset_case(16,0,0),-2,'out-of-storage animation offset');
for(const row of proof.cases){
 const label=JSON.stringify(row);assert.equal(c.run(row.op,row.slot,row.hidden,row.facing,row.program,row.script),0,label);
 assert.deepEqual(Array.from({length:8},(_,i)=>c.state(i)>>>0),row.state,label+' enemy');
 assert.equal(c.meta(0),+row.oldDeleted,label+' deletion');assert.equal(c.meta(1),row.handle,label+' handle');
 assert.equal(c.meta(2),+!!row.vm.length,label+' creation');
 if(row.vm.length){assert.deepEqual(Array.from({length:11},(_,i)=>c.vm_word(i)>>>0),row.vm,label+' VM');assert.equal(c.meta(3),+(row.registry[0]==='0x47e950'),label+' registry');}
}
assert.equal(c.reject_legacy(),0,'unported TH14 command must not run the old number');
for(const r of proof.rgbTimelines){assert.equal(c.rgb_interp_case(r.mode,r.duration,r.rate,...r.target),0,JSON.stringify(r));for(let j=0;j<r.frames.length;++j){if(j)assert.equal(c.scale_interp_tick(),0,`rgb mode ${r.mode} frame ${j}`);assert.deepEqual(Array.from({length:20},(_,n)=>c.rgb_interp_value(n)>>>0),r.frames[j],`rgb mode ${r.mode} duration ${r.duration} rate ${r.rate} target ${r.target} frame ${j}`);}}
for(const r of proof.colors){assert.equal(c.color_case(r.op,r.slot,r.present,r.value),0,JSON.stringify(r));assert.deepEqual(Array.from({length:5},(_,n)=>c.color_value(n)>>>0),r.result,JSON.stringify(r));assert.deepEqual(r.reads,r.slot>=0&&r.slot<16&&r.present?(r.op===325?[0,3,2,1]:[0,1]):[0]);}
for(const r of proof.alphaTimelines){assert.equal(c.alpha_interp_case(r.op,r.mode,r.duration,r.rate,r.start,r.target),0,JSON.stringify(r));for(let j=0;j<r.frames.length;++j){if(j)assert.equal(c.scale_interp_tick(),0,`alpha op ${r.op} mode ${r.mode} frame ${j}`);assert.deepEqual(Array.from({length:12},(_,n)=>c.alpha_interp_value(n)>>>0),r.frames[j],`alpha op ${r.op} mode ${r.mode} duration ${r.duration} rate ${r.rate} start ${r.start} frame ${j}`);}}
for(const r of proof.scaleTimelines){assert.equal(c.scale_interp_case(r.mode,r.duration,r.rate,...r.target),0,JSON.stringify(r));for(let j=0;j<r.frames.length;++j){if(j)assert.equal(c.scale_interp_tick(),0,`scale mode ${r.mode} frame ${j}`);assert.deepEqual(Array.from({length:16},(_,n)=>c.scale_interp_value(n)>>>0),r.frames[j],`scale mode ${r.mode} duration ${r.duration} rate ${r.rate} frame ${j}`);}}
for(const r of proof.scales){assert.equal(c.scale_case(r.op,r.slot,r.present,r.x,r.y),0,JSON.stringify(r));assert.deepEqual(Array.from({length:6},(_,n)=>c.scale_value(n)>>>0),r.result,JSON.stringify(r));assert.deepEqual(r.reads,r.slot>=0&&r.slot<16&&r.present?[0,2,1]:[0]);}
for(const r of proof.angled){assert.equal(c.angled_case(r.file,r.program,...r.position,r.angle),0,JSON.stringify(r));assert.deepEqual(Array.from({length:12},(_,n)=>c.angled_value(n)>>>0),r.vm,JSON.stringify(r));assert.equal(c.meta(3),1);assert.deepEqual(r.reads,[1,0,2]);assert.deepEqual(r.bindings,[1]);assert.deepEqual(r.registry,['0x47e950']);}
for(const r of proof.offsetEffects){assert.equal(c.offset_effect_case(r.file,r.program,...r.position,r.angle),0,JSON.stringify(r));assert.deepEqual(Array.from({length:12},(_,n)=>c.angled_value(n)>>>0),r.vm,JSON.stringify(r));assert.equal(c.meta(3),1);assert.deepEqual(r.reads,[3,2,4,1,0]);assert.deepEqual(r.bindings,[1]);assert.deepEqual(r.registry,['0x47e950']);}
for(const r of proof.logos){
 assert.equal(c.logo_case(r.mode,r.flags,r.program),0,JSON.stringify(r));assert.equal(c.meta(2),+!!r.vm.length,JSON.stringify(r));
 if(r.vm.length){assert.deepEqual(Array.from({length:11},(_,i)=>c.vm_word(i)>>>0),r.vm,JSON.stringify(r));assert.equal(c.logo_appended(),1);assert.deepEqual(r.bindings,[0]);assert.deepEqual(r.registry,['0x47e890']);}
}
for(const row of proof.positions){
 const label=JSON.stringify(row);assert.equal(c.position_case(row.world,row.rotation,row.velocity,row.parent),0,label);
 assert.equal(c.position_value(16,0)>>>0,row.angle,label+' angle');
 for(let n=0;n<16;++n)assert.deepEqual(Array.from({length:5},(_,i)=>c.position_value(n,i)>>>0),row.vms[n],label+' slot '+n);
}
for(const row of proof.directions){
 const label=JSON.stringify(row);assert.equal(c.direction_case(row.prior,row.vx,row.facing),0,label);
 assert.equal(c.direction_value(0)>>>0,row.direction,label+' direction');assert.equal(c.meta(1),row.handle,label+' handle');
 assert.equal(c.meta(0),+row.oldDeleted,label+' deletion');assert.equal(c.meta(2),+!!row.vm.length,label+' creation');
 if(row.vm.length){assert.deepEqual([c.vm_word(0)>>>0,c.vm_word(1)>>>0,...[3,4,5].map(i=>c.vm_word(i)>>>0)],row.vm,label+' VM');
 assert.equal(c.direction_value(1),row.bindings[0],label+' script');assert.equal(c.direction_value(2),+(row.registry[0]==='0x47e890'),label+' registry');}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const r of proof.rotations){assert.equal(c.rotation_case(r.slot,r.present,r.angle),0,JSON.stringify(r));assert.deepEqual(Array.from({length:3},(_,i)=>c.rotation_value(i)>>>0),r.result,JSON.stringify(r));assert.deepEqual(r.reads,r.slot>=0&&r.slot<16&&r.present?[0,1]:[0]);}
const report={passed:true,rgbInterpolationTimelines:proof.rgbTimelines.length,rgbInterpolationFrames:proof.rgbTimelines.reduce((n,r)=>n+r.frames.length,0),cases:proof.cases.length,colorCases:proof.colors.length,alphaInterpolationTimelines:proof.alphaTimelines.length,alphaInterpolationFrames:proof.alphaTimelines.reduce((n,r)=>n+r.frames.length,0),scaleInterpolationTimelines:proof.scaleTimelines.length,scaleInterpolationFrames:proof.scaleTimelines.reduce((n,r)=>n+r.frames.length,0),scaleCases:proof.scales.length,angledEffectCases:proof.angled.length,rotations:proof.rotations.length,positions:proof.positions.length,directions:proof.directions.length,stageLogoCases:proof.logos.length,nativeExecutableSha256:proof.executableSha256,
 scope:'TH14 ECL 326 RGB interpolation: 1224 timelines compare actual 42db70 setup and 473af0/473df0 dynamics for all 32 modes plus default -1/32, four duration cases, three rates and three RGB targets. Tangents are cleared, alpha is preserved, each Hermite product is truncated separately, RGB bytes wrap as in retail. TH14 ECL 325/327/331/336 color, alpha and layer setters: 320 native cases with slot bounds, missing handles, byte truncation, unchanged other channels and flags. ECL 328/332 primary/secondary alpha interpolation: 2448 timelines compare actual setters 42d9b0/42d900 and 473af0/474190 dynamics for all 32 modes plus default -1/32, negative/zero/one/35-frame durations, three rates and three start/target pairs; primary tangent clearing, secondary tangent preservation and blend-mode switch agree. Integer output is converted once after rounded SSE operations. TH14 ECL 330 scale interpolation: 816 timelines compare actual 42dd70 setup and 473af0/474750 dynamics and actual easing 4041a0 / sine 4a8020 against production ANM updates, all 32 retail modes and two default cases (-1, 32), negative/zero/one/35-frame durations, three rates and two targets; timer/start/end/tangents and scale bits agree. TH14 ECL 329/335 scale and scale-velocity setters (160 cases, slot bounds/stale handles, reverse argument read order and dirty flags), ECL 315 angled effect creation (189 cases, three resources, first ANM update before position/angle overwrite, signed zero/NaN/infinity), ECL 319 slot-local rotation, flags and stale-handle clearing; ECL 303/306/307/308/313/316/318 creation/replacement, base-script selection/restoration, flags, sixteen slots, layer/origin and first ANM update; sixteen-slot position synchronization, native direction changes and ECL 554 stage-logo guard/creation. Argument reads, allocation, resource binding and registry lookup are controlled boundaries. Complete resource template caching and alternate-mode frontend wiring are not covered.',
 legacyRouteRefusal:true,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,...['Interpolation.cpp','Interpolation.hpp','AnmInterpreter.cpp','EnemyAnimations.cpp','EnemyScript.cpp','AnmManager.cpp','AnmManager.hpp','EnemyState.hpp'].map(p=>'cpp/game/'+p)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-enemy-animation-native.py','tools/th14-enemy-animation-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
report.offsetCases=proof.offsets.length;report.scope+=' ECL 320 is the retail per-slot animation offset setter at 4253c0; X/Y raw float values and forced-zero Z agree, including sentinels, NaN and infinity. Tests traverse the production ECL route; the native argument readers are boundaries.';
report.offsetEffectCases=proof.offsetEffects.length;report.scope+=' ECL 337 at 425581: 189 actual handler/ANM first-update comparisons, XYZ position plus offsets and rotation installed before first update, including rotation overwritten by the script, signed zero, NaN and infinity; reverse argument read order [3,2,4,1,0]. Resource binding and allocation remain controlled boundaries.';
writeFileSync(resolve(root,'docs/porting/th14-enemy-animation-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} animation commands, ${proof.positions.length} position, ${proof.directions.length} direction and ${proof.logos.length} stage-logo cases, ${proof.angled.length} angled effects and ${proof.scales.length} scale cases, ${report.rgbInterpolationTimelines} RGB timelines / ${report.rgbInterpolationFrames} frames, ${report.colorCases} color cases, ${report.alphaInterpolationTimelines} alpha timelines / ${report.alphaInterpolationFrames} frames, ${report.scaleInterpolationTimelines} scale timelines / ${report.scaleInterpolationFrames} frames, strict dispatch regression.`);
