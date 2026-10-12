import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);assert.equal(c.open_title(),1);
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-end-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const state=n=>n===30||n===24?21:n===25?22:n===26?23:n===29?26:n===32?27:n;
const compare=(r,label)=>{
 const n=r.result;assert.deepEqual(Array.from({length:7},(_,i)=>c.spell_end_value(i)),[state(n.state),n.selected,n.previous,n.count,n.depth,n.disabled,n.timer+1],label);
 assert.deepEqual(Array.from({length:c.spell_end_value(7)},(_,i)=>c.spell_end_sound(i)),n.events.filter(e=>e[0]==='sound').map(e=>e[1]),`${label} sounds`);
 assert.deepEqual(Array.from({length:c.spell_end_value(8)},(_,i)=>c.results_probe_creation(i,0)).filter((_,i)=>c.results_probe_creation(i,4)===0),n.events.filter(e=>e[0]==='create').map(e=>e[1]),`${label} bindings`);
 assert.equal(c.spell_end_value(10),n.recordChanged?1:0,`${label} records`);
 const destination=n.destination===10?3:n.destination===2||n.destination===4?2:0;assert.equal(c.spell_end_value(9),destination,`${label} exit action`);
};
for(const [i,r] of native.entries.entries()){assert.equal(c.spell_end_setup(r.completed,21,r.timer,2),1);assert.equal(c.spell_end_tick(0,0),1);compare(r,`entry${i}`);}
for(const [i,r] of native.controls.entries()){assert.equal(c.spell_end_setup(r.completed,22,17,r.selected),1);assert.equal(c.spell_end_tick(r.pressed,r.repeat),1);compare(r,`control${i}`);}
for(const [i,r] of native.exits.entries()){assert.equal(c.spell_end_setup(r.completed,26,r.timer,r.selected),1);assert.equal(c.spell_end_tick(0,0),1);compare(r,`exit${i}`);}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-spell-end-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,entries:native.entries.length,controls:native.controls.length,exits:native.exits.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production uses original ANMs, compares root bindings, state/cursor/history/clock, sounds, unchanged score records and exit requests; opaque ANM interrupt/hide and file services are excluded.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/PauseEnd.cpp','runtimes/th12/th12_web/cpp/game/PauseMenu.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-spell-end-native.py','tools/th14-spell-end-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${native.entries.length} spell result entries / ${native.controls.length} controls / ${native.exits.length} exits`);
