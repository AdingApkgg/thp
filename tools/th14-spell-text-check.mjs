import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/spell-text-check');mkdirSync(out,{recursive:true});
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-spell-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-text-native.json'),'utf8')),sources=['cpp/game/SpellController.cpp','cpp/game/GameEconomy.cpp','cpp/game/HudTh14Text.cpp','cpp/game/SpellTiming.cpp','cpp/game/AsciiText.cpp','cpp/game/AnmVm.cpp','tests/cpp/th14-spell-text-fixture.cpp','tests/cpp/th14-hud-text-fixture.cpp'],path=resolve(out,'spell-text.wasm');assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',...sources.filter(p=>p!=='tests/cpp/th14-hud-text-fixture.cpp'),'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;let glyphs=0,requests=0;
for(const [n,r] of native.rows.entries()){
 assert.equal(c.spell_text_run(r.selection,r.flags,r.runFlags,r.id,r.bonus,r.captures,r.attempts,r.alpha,r.live),r.glyphs.length,`layout${n} glyph count`);assert.equal(c.request_count(),r.requests.length);
 for(const [i,q] of r.requests.entries()){let text='';for(let k=0;k<64;++k){const v=c.request_byte(i,k);if(!v)break;text+=String.fromCharCode(v);}assert.equal(text,q.text);assert.deepEqual(Array.from({length:3},(_,k)=>c.request_word(i,k)>>>0),[q.font,q.passIndex,q.color]);++requests;}
 for(const [i,g] of r.glyphs.entries()){assert.deepEqual([c.word(i,0)|0,c.word(i,1)>>>0,c.word(i,2)],[g.sprite,g.color,+g.filtered]);assert.equal(c.real(i,0),g.x);assert.equal(c.real(i,1),g.y);++glyphs;}
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-spell-text-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,glyphs,requests,wasmSha256:sha(bytes),nativeExecutableSha256:native.executableSha256,scope:native.scope+' Production liveness gate is controlled, not actual GameBattle title-handle integration.',sourceHashes:Object.fromEntries([...sources,'cpp/game/SpellController.hpp','cpp/game/GameBattle.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-spell-text-check.mjs','tools/th14-spell-text-native.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS ${native.rows.length} original spell bonus/history layouts; ${requests} requests; ${glyphs} glyphs exact`);
