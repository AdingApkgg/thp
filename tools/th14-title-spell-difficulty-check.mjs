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
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/title-spell-difficulty-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const setup=(state,timer,r,resume=-1)=>assert.equal(c.spell_select_setup(19,state,timer,r.stage,r.row,r.selected??0,r.loadout??0,1,resume),1);
const text=p=>{const mem=new Uint8Array(c.memory.buffer);return Buffer.from(mem.subarray(p,mem.indexOf(0,p))).toString('hex');};let fontRequests=0,asciiRequests=0;
const compare=(r,label)=>{
 const names=['screen','substate','selected','count','depth','loadout','stage','row','resumeRow','resume','disabled'];
 for(let n=0;n<names.length;++n)assert.equal(c.spell_select_value(n)>>>0,r[names[n]],`${label} ${names[n]}`);
 assert.deepEqual(Array.from({length:5},(_,n)=>c.spell_select_choice(n)>>>0),r.choices,`${label} choices`);
 assert.deepEqual(Array.from({length:c.records_probe_value(10)},(_,n)=>c.records_probe_sound(n)),r.events.filter(e=>e[0]==='sound').map(e=>e[1]),`${label} sounds`);
 assert.equal(c.records_probe_value(9),r.texts.length,`${label} fonts`);
 for(const [i,v] of r.texts.entries()){assert.equal(text(c.records_probe_text(i)),v.text,`${label} font ${i}`);assert.deepEqual(Array.from({length:5},(_,n)=>c.spell_select_text_value(i,n)>>>0),[v.color,v.offset,v.font,v.style,v.row]);++fontRequests;}
 assert.equal(c.spell_launch_value(8),Number(r.events.some(e=>e[0]==='fade')),`${label} fade`);
 if(r.spell!==0xffffffff){assert.equal(c.spell_select_value(11),1,`${label} start`);assert.deepEqual(Array.from({length:8},(_,n)=>c.spell_launch_value(n)>>>0),[r.spell,r.gameStage,r.character,r.partner,r.difficulty,r.resumeStage,r.resumeRow,r.resume],`${label} launch`);}
};
const tick=pressed=>assert.equal(c.results_probe_tick(pressed,0),1);
for(const [i,r] of native.entries.entries()){setup(0,0,r,r.resume);tick(0);compare(r.result,`entry ${i}`);}
for(const [i,r] of native.controls.entries()){setup(2,17,r);tick(r.pressed);compare(r.result,`control ${i}`);}
for(const [i,r] of native.boundaries.entries()){setup(r.state,r.timer,r);tick(0);compare(r.result,`boundary ${i}`);}
const bits=x=>{const b=Buffer.alloc(4);b.writeFloatLE(x);return b.readUInt32LE();};
for(const [i,r] of native.layouts.entries()){setup(2,17,r);assert.equal(c.replay_text_queue(),r.ascii.length);for(const [n,v] of r.ascii.entries()){assert.equal(text(c.results_text_bytes(n)),v.text,`layout ${i}/${n}`);assert.deepEqual(Array.from({length:8},(_,k)=>c.results_text_value(n,k)>>>0),[...v.position.map(bits),v.color,v.shadow,v.font,...v.scale.map(bits)],`layout ${i}/${n} style`);++asciiRequests;}}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-title-spell-difficulty-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,entries:native.entries.length,controls:native.controls.length,boundaries:native.boundaries.length,layouts:native.layouts.length,fontRequests,asciiRequests,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production original title ANMs; state/choice/history/start parameters and exact font/ASCII request words compared. Native ANM interruptions and GPU excluded.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/TitleTh14.cpp','runtimes/th12/th12_web/cpp/game/TitleMenu.hpp','runtimes/th12/th12_web/cpp/game/TitleText.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-title-spell-difficulty-native.py','tools/th14-title-spell-difficulty-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.entries.length} difficulty entries, ${native.controls.length} controls, ${native.boundaries.length} boundaries, ${native.layouts.length} layouts/${fontRequests} fonts/${asciiRequests} ASCII`);
