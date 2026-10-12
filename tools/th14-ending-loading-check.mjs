import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);assert.equal(c.open_title(),1);
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ending-loading-native.json'),'utf8'));assert.equal(native.passed,true);
const state=()=>Array.from(new Uint32Array(c.memory.buffer,c.ending_loading_state(),14));
let pendingFrames=0;
for(const [index,row] of native.rows.entries()){
 assert.equal(c.ending_loading_begin(row.slot,row.rate,row.seen),1);
 assert.equal(c.ending_loading_resource(0),0,'ending ANMs are undecoded before their actual opcode7');
 assert.equal(c.ending_loading_tick(),1);assert.deepEqual(state(),row.requested,`request${index}`);assert.equal(c.ending_loading_resource(1),1);assert.notEqual(c.ending_loading_resource(2),0);
 for(const expected of row.pending){assert.equal(c.ending_loading_tick(),1);assert.deepEqual(state(),expected,`pending${index}`);assert.equal(c.ending_loading_resource(0),0);++pendingFrames;}
 assert.equal(c.ending_loading_complete(),1);assert.deepEqual(state(),row.completed,`complete${index}`);assert.equal(c.ending_loading_resource(0),1);assert.equal(c.ending_loading_resource(1),0);assert.equal(c.ending_loading_resource(2),0);assert.equal(c.ending_loading_resource(3),1,'real ANM negative-time templates ready before interpreter resume');
 assert.equal(c.ending_loading_tick(),1);assert.deepEqual(state(),row.resumed,`resume${index}`);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-ending-loading-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,pendingFrames,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production original e01.anm stays undecoded until the actual resource job; compares all fourteen callback/instruction/timer words and real loading root lifetime, then initializes actual slot templates before resume. Controlled service fixture, no GPU/audio or natural full ending proof. Browser uses one main-thread resource decode/upload/template job after a pending ending callback; complete native thread scheduling is excluded.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/Ending.cpp','runtimes/th12/th12_web/cpp/game/Ending.hpp','runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/cpp/game/GameSessionResources.hpp','runtimes/th12/th12_web/cpp/sdl/Application.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-ending-loading-native.py','tools/th14-ending-loading-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} ending resource waits; ${pendingFrames} pending callbacks match retail timer/flags/instruction state`);
