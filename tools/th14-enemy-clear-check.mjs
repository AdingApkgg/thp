import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-clear-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-enemy-clear-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-enemy-clear-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'clear.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-clear-native.json'),'utf8'));
for(const row of proof.metadata){c.metadata(row.file,row.script,row.override,row.id);assert.deepEqual(Array.from({length:3},(_,n)=>c.meta_value(n)>>>0),row.result,JSON.stringify(row));}
const bits=f=>new Uint32Array(new Float32Array([f]).buffer)[0];
for(const row of proof.cases){
 const p=c.allocate(36);new Uint32Array(c.memory.buffer,p,9).set(row.inputs.flatMap(r=>[r.flags,...r.position.map(bits)]));
 try{assert.equal(c.run(row.rate,p),0,JSON.stringify(row));
  assert.deepEqual(Array.from({length:3},(_,j)=>Array.from({length:17},(_,n)=>c.value(j,n)>>>0)),row.result,JSON.stringify(row));
  assert.deepEqual(Array.from({length:3},(_,n)=>c.timer_value(n)>>>0),row.timer);
  assert.deepEqual(Array.from({length:c.sound_size()},(_,n)=>c.sound_value(n)>>>0),row.sounds.flat());
  assert.deepEqual([c.rng_value(0),c.rng_value(1)],row.rng);
  assert.equal(c.effect_size(),row.effects.length);
  for(let j=0;j<row.effects.length;j++){const r=row.effects[j];assert.deepEqual(Array.from({length:8},(_,n)=>c.effect_value(j,n)>>>0),[...r.slice(0,6),0x20200,8],JSON.stringify(row));assert.equal(r[6],0);assert.equal(r[7],0x77770008);}
 }finally{c.release(p);}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/EnemyManager.cpp','cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyAnimations.cpp','cpp/game/EnemyFrame.cpp','cpp/game/AnmManager.cpp','cpp/game/EnemyState.hpp'];
for(const r of proof.sounds){assert.equal(c.sound_case(r.id,r.x),0);assert.deepEqual(Array.from({length:c.sound_size()},(_,i)=>c.sound_value(i)>>>0),r.result.flat());}
for(const r of proof.inactiveSpells){assert.equal(c.inactive_spell_case(r.healthFlags,r.spellFlags),0);assert.deepEqual([c.inactive_spell_value(0)>>>0,c.inactive_spell_value(1)>>>0],r.result);}
assert.equal(c.inactive_spell_case(0xffffffff,1),-2,'active spell requires native score/visual port');
assert.equal(proof.emptyLaser545,true);assert.equal(c.empty_laser_gate(0),0);assert.equal(c.empty_laser_gate(1),-2,'this fixture has an unsupported line laser; curve resets are verified separately');
const report={passed:true,spawnMetadataCases:proof.metadata.length,clearingCases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'TH14 post-spawn death metadata and ECL 525 three-enemy traversal, eligibility mask, thirteen-count drop reset, zero-drop RNG, sound/effect delivery order and manager timer. Native 424cb0, 424af0 and zero-count 4215b0 execute; sound and effect factory are controlled delivery boundaries. Optional death subroutine/callback paths, nonzero item drops and GPU rendering are not covered.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
report.sound516Cases=proof.sounds.length;report.scope+=' ECL 516 sound ID and source X delivery are verified at the native audio queue boundary.';
report.inactiveSpell523Cases=proof.inactiveSpells.length;report.scope+=' ECL 523 inactive-spell guard and enemy health flag clear are verified; active-spell ending is verified separately by th14-spell-verified.json and result animation requests by th14-hud-notice-verified.json.';
report.emptyLaser545=true;report.scope+=' ECL 545 executes the retail empty-list laser reset; this fixture refuses its unsupported line-laser cancellation; curve lists are verified separately by th14-laser-curve-manager-verified.json.';
writeFileSync(resolve(root,'docs/porting/th14-enemy-clear-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.spawnMetadataCases} metadata, ${report.clearingCases} three-enemy clear and ${report.sound516Cases} sound cases.`);
