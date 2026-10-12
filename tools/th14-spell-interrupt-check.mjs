import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');if(!process.argv.includes('--skip-build'))execFileSync(process.execPath,['tools/th14-startup-session-check.mjs'],{cwd:root,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(resolve(root,'artifacts/th14/startup-session/startup.wasm')),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-interrupt-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [i,r] of native.rows.entries()){assert.equal(c.spell_interrupt_run(r.flags,r.boss,r.slot,r.health,r.time),0,`case ${i}`);assert.deepEqual([c.spell_interrupt_word(r.slot,0)>>>0,c.spell_interrupt_word(r.slot,1)>>>0],r.result,`case ${i}`);assert.deepEqual([text(c.spell_interrupt_name(r.slot,0)),text(c.spell_interrupt_name(r.slot,1))],r.names,`case ${i} names`);}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-spell-interrupt-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,cases:native.rows.length,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope,sources:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/EnemyTh14Commands.cpp','runtimes/th12/th12_web/tests/cpp/th14-startup-fixture.cpp','tools/th14-spell-interrupt-native.py','tools/th14-spell-interrupt-check.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');console.log(`PASS ${native.rows.length} ordinary/spell-practice interrupt assignments`);
