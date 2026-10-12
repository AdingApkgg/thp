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
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/title-replay-text-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const bits=x=>{const b=Buffer.alloc(4);b.writeFloatLE(x);return b.readUInt32LE();};const copy=hex=>{const b=Buffer.from(hex,'hex'),p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const catalog=native.catalog.map(entry=>entry?{header:copy(entry.header),mask:entry.mask,stages:copy(entry.stages)}:null);let requests=0;
for(const [ordinal,row] of native.rows.entries()){
 assert.equal(c.replay_text_setup(row.state,row.timer,row.fraction,row.selected,row.page,row.file),1);
 for(const [index,entry] of catalog.entries())assert.equal(c.replay_text_entry(index,entry?.header??0,entry?.mask??0,entry?.stages??0),1,`catalog ${index}`);
 assert.equal(c.replay_text_queue(),row.requests.length);
 for(let i=0;i<row.requests.length;++i){const r=row.requests[i],p=c.results_text_bytes(i),mem=new Uint8Array(c.memory.buffer);assert.equal(Buffer.from(mem.subarray(p,mem.indexOf(0,p))).toString('hex'),r.text,`layout ${ordinal}, request ${i}: text`);assert.deepEqual(Array.from({length:8},(_,n)=>c.results_text_value(i,n)>>>0),[...r.position.map(bits),r.color,r.shadow,r.font,...r.scale.map(bits)],`layout ${ordinal}, request ${i}: style`);++requests;}
}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-title-replay-text-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,layouts:native.rows.length,requests,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production ReplayRecorder encrypt/compress then Replay::open decrypt/parse every test recording, followed by actual TitleMenu::queue_ascii; every text byte and eight position/style words compared.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/TitleText.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-title-replay-text-native.py','tools/th14-title-replay-text-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${native.rows.length} original Replay layouts, ${requests} ASCII requests exact`);
