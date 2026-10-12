import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/music-request-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
let stage=0;
for(const [i,r] of native.rows.entries()){
 if(stage!==r.stage){stage=r.stage;assert.equal(c.music_request_begin(stage),1,string(c.error()));}
 assert.equal(c.music_request_run(r.id,r.replay,r.stop,r.match),1,`request ${i}`);
 const events=Array.from({length:c.music_request_value(0)},(_,n)=>['audio',c.music_request_event(n,0),c.music_request_event(n,1)]);
 for(let n=0;n<c.music_request_value(1);++n)events.push(['front',c.results_probe_creation(n,0)]);
 assert.deepEqual(events,r.events,`request ${i}`);assert.equal(c.music_request_value(2),1,`retained dialogue ${i}`);
 assert.deepEqual(Array.from(new Uint8Array(c.memory.buffer,c.music_request_unlocks(),18)),r.unlocks,`unlock ${i}`);
}
for(const r of native.results)assert.equal(c.music_result_request(r.flags),r.events[0][0]==='failure'?1:2,`result ${r.flags}`);
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-music-request-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,musicRequests:native.rows.length,resultBranches:native.results.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production event order, original front ANM script, score unlock bytes and retained MSG owner checked. SDL audio playback, initial stage music, waveform and complete result menus excluded.',sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/GameBattle.cpp','runtimes/th12/th12_web/cpp/game/GameBattle.hpp','runtimes/th12/th12_web/cpp/game/GameSession.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-music-request-native.py','tools/th14-music-request-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${native.rows.length} music requests and ${native.results.length} result dispatch branches`);
