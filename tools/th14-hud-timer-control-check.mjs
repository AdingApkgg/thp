import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..');
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-timer-control-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/hud-timer-check/timer.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-timer-control-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [n,r] of native.rows.entries()){
 assert.equal(c.control_run(r.seconds,r.previous,r.mode,r.flags,r.y,r.gate,r.resources),1,`entry ${n}`);assert.deepEqual(Array.from({length:6},(_,k)=>c.control_value(k)>>>0),r.state,`entry ${n} state`);
 assert.deepEqual([c.control_value(6),c.control_value(7)],[r.updates.filter(v=>v[0]===0).length,r.updates.filter(v=>v[0]===1).length],`entry ${n} immediate updates`);
 const sprites=[-1,-1];for(const [i,v] of r.sprites)sprites[i]=v;assert.deepEqual([c.control_value(8)|0,c.control_value(9)|0],sprites,`entry ${n} sprites`);
 assert.deepEqual(Array.from({length:c.value(5)},(_,k)=>c.sound(k)),r.sounds,`entry ${n} sounds`);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=['runtimes/th12/th12_web/tests/cpp/th14-hud-timer-fixture.cpp','runtimes/th12/th12_web/cpp/game/Hud.cpp','runtimes/th12/th12_web/cpp/game/Hud.hpp','runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.cpp','tools/th14-hud-timer-control-native.py','tools/th14-hud-timer-control-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-timer-control-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production timer_th14 with stopped scripts consumes immediate interruption labels and advances age; observes update counts, final pending and visibility/state/sprite/audio. Immediate update label order is source-wired, only counts are asserted here.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} original countdown visibility/mode cases exact`);
