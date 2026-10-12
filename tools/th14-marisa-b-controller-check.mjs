import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/marisa-b-controller-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-marisa-b-controller-native.py',{cwd:root,stdio:'inherit',windowsHide:true});execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-sakuya-b-controller-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'controller.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/marisa-b-controller-native.json'),'utf8'));
const events=()=>Array.from({length:c.event_count()},(_,i)=>Array.from({length:c.event_size(i)},(_,k)=>c.event(i,k)>>>0));
for(const r of proof.start){const why=JSON.stringify(r);assert.equal(c.start_selection(3,r.flags,r.time),0,why);assert.deepEqual(Array.from({length:5},(_,n)=>c.value(n)>>>0),r.result,why);
 assert.deepEqual(events(),[[1,44,1],[1,49,0]],why);assert.equal(c.created(),2,why);
 const actual=Array.from({length:2},(_,i)=>['animation',c.script(i),...[0,1,2].map(a=>c.position(i,a)>>>0)]);
 assert.deepEqual(actual,r.events.filter(e=>e[0]==='animation'),why);
}
const kinds={sound:1,freeze:2,cancel:3,circle:4};
for(const r of proof.ticks){const why=JSON.stringify(r);assert.equal(c.tick_selection(3,r.time,r.active,+r.missing,r.rate,+r.dialogue,+r.advanced),1,why);
 const actual=Array.from({length:10},(_,n)=>n===1?+!!c.tick_value(n):c.tick_value(n)>>>0),expected=r.result.map((v,n)=>n===1?+!!v:v);assert.deepEqual(actual,expected,why);
 assert.deepEqual(events(),r.events.map(e=>[kinds[e[0]],...e.slice(1)]),why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-marisa-b-controller-verified.json'),JSON.stringify({passed:true,startCases:proof.start.length,tickCases:proof.ticks.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail 412e80 startup and 412200 common update through actual 412fb0/4130e0 versus production BombController selection 3: spell flags/bonus, used-Bomb count, invincibility, raw animation position/scripts, common positional sound 44 and sound 49, clock rates, inactive/nonzero states, missing main animation and auxiliary interrupt, float acceleration/position, scale-derived radius, four-frame damage-circle request, frame-180 interrupt/cancel, frame-500/dialogue finish and reward-2 cancel requests. Empty native bullet/laser lists; ANM factories/audio/cancel delivery are controlled. Stock/HUD/common activation gate, actual bullet/laser effects, complete lifecycle and GPU pixels are separate.',sourceHashes:Object.fromEntries([fixture,'cpp/game/BombController.cpp','cpp/game/BombController.hpp','cpp/game/PlayerMotion.cpp','cpp/game/AnmManager.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-marisa-b-controller-native.py','tools/th14-sakuya-b-controller-native.py','tools/th14-marisa-b-controller-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');console.log(`PASS: ${proof.start.length} Marisa B startup and ${proof.ticks.length} common tick cases.`);
