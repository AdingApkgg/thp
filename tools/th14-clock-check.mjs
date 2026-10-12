import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/clock-native.json'),'utf8'));
for(const r of proof.rows){assert.equal(r.clock,r.ticks);const p=c.clock_apply(r.ticks,r.calls);assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,p,4)),r.words);}
const fonts=JSON.parse(readFileSync(resolve(root,'artifacts/th14/font-initialization-native.json'),'utf8')),scores=JSON.parse(readFileSync(resolve(root,'artifacts/th14/score-native.json'),'utf8'));let constructors=0;
for(const font of fonts.rows.filter(r=>r.calls===0&&r.firstSuccess)){const score=scores.cases.find(r=>r.seed===font.seed&&r.calls===0);if(!score)continue;
 for(const high of [0,0x10000,0xffff0000]){const p=c.clock_construct((high+font.seed)>>>0);assert.equal(Buffer.from(new Uint8Array(c.memory.buffer,p,256)).toString('hex'),font.noise);assert.deepEqual(Array.from({length:4},(_,n)=>c.clock_construct_state(n)>>>0),[font.finalSeed,font.finalCalls,score.finalSeed,score.finalCalls]);++constructors;}
}
assert.equal(constructors,12);const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-clock-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,constructors,wasmSha256:sha(bytes),nativeExecutableSha256:proof.executableSha256,scope:proof.scope+' Twelve production constructors compare actual font-table bytes plus both final streams against independently observed retail font/score initialization. Headless default input remains0; browser passes actual performance.now() milliseconds, unsigned32 wrapped. Browser clock is not Windows uptime; captured seed/count and loading duration are never forced.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/ClockSeedTh14.hpp','runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/GameSession.hpp','runtimes/th12/th12_web/cpp/sdl/Application.cpp','tools/th14-clock-native.py','tools/th14-clock-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${proof.rows.length} retail clock stores and ${constructors} complete initialization constructors`);
