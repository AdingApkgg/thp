import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..');
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-timer-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-timer-text-native.json'),'utf8'));
assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const bytes=readFileSync(resolve(root,'artifacts/th14/hud-timer-check/timer.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
let requests=0;for(const [n,r] of native.rows.entries()){
 assert.equal(c.text_run(r.gate,r.seconds,r.hundredths,...r.position,r.color),r.requests.length,`layout ${n} count`);
 for(const [i,q] of r.requests.entries()){
  let text='';for(let k=0;k<32;k++){const v=c.text_byte(i,k);if(!v)break;text+=String.fromCharCode(v);}
  assert.equal(text,q.text,`layout ${n}/${i} bytes`);assert.deepEqual(Array.from({length:8},(_,k)=>c.text_word(i,k)>>>0),q.words,`layout ${n}/${i} style/position`);++requests;
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=['runtimes/th12/th12_web/cpp/game/HudTh14Boss.cpp','runtimes/th12/th12_web/cpp/game/Hud.cpp','runtimes/th12/th12_web/cpp/game/Hud.hpp','runtimes/th12/th12_web/tests/cpp/th14-hud-timer-fixture.cpp','tools/th14-hud-timer-text-native.py','tools/th14-hud-timer-text-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-hud-timer-text-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,requests,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production timer_text_th14 directly invoked with controlled digit VM script-position/color. Absent manager maps to absent boss in the production environment. Other HUD text/layout, font atlas pixels and animated frame sampling are separate integrations.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} original timer layouts; ${requests} ASCII requests exact`);
