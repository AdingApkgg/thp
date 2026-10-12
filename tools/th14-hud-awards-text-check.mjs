import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/hud-awards-text-check');mkdirSync(out,{recursive:true});
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-hud-awards-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/hud-awards-text-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const sources=['cpp/game/HudTh14Text.cpp','cpp/game/AsciiText.cpp','cpp/game/AnmVm.cpp','cpp/game/SpellTiming.cpp','tests/cpp/th14-hud-text-fixture.cpp'],path=resolve(out,'awards.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;let glyphs=0,requests=0;
for(const [n,r] of native.rows.entries()){
 assert.equal(c.awards_run(r.result===1?1:0,r.time===2&&r.show&&r.manager?1:0,r.bonus,r.frames,r.encoded,r.alpha),r.glyphs.length,`layout ${n} glyph count`);
 assert.equal(c.request_count(),r.requests.length,`layout ${n} queue count`);
 for(const [i,q] of r.requests.entries()){
  let text='';for(let k=0;k<64;k++){const v=c.request_byte(i,k);if(!v)break;text+=String.fromCharCode(v);}
  assert.equal(text,q.text,`layout ${n}/${i} bytes`);assert.deepEqual(Array.from({length:3},(_,k)=>c.request_word(i,k)>>>0),[q.font,q.passIndex,q.color],`layout ${n}/${i} queue style`);++requests;
 }
 for(const [i,g] of r.glyphs.entries()){
  assert.deepEqual([c.word(i,0)|0,c.word(i,1)>>>0,c.word(i,2)], [g.sprite,g.color,+g.filtered],`layout ${n} glyph ${i} style`);
  assert.equal(c.real(i,0),g.x,`layout ${n} glyph ${i} x`);assert.equal(c.real(i,1),g.y,`layout ${n} glyph ${i} y`);++glyphs;
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-hud-awards-text-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,requests,glyphs,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production th14_hud_awards called with result/time liveness booleans from controlled handle/manager conditions; grouped result center translated to left queue origin and all glyph X/Y words exact. Queue byte/font/pass/color compared. Missing-handle lifecycle is not asserted; actual Hud.queue_text wiring and real GameSession draw require separate integration.',sourceHashes:Object.fromEntries([...sources,'cpp/game/HudTh14Text.hpp','cpp/game/Hud.cpp','cpp/game/SpellTiming.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-hud-awards-text-native.py','tools/th14-hud-awards-text-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} original awards/time layouts; ${requests} requests; ${glyphs} glyphs exact`);
