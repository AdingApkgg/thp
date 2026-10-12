import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/spell-notice-animation-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-spell-notice-animation-native.py',{cwd:root,env,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-spell-notice-animation-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),path=resolve(out,'notice-animation.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'),'utf8'));
const files=['front.anm','ascii.anm'].map(n=>resolve(root,archive.extraction,n));for(const [n,p] of files.entries()){const b=readFileSync(p),ptr=c.allocate(b.length);new Uint8Array(c.memory.buffer,ptr,b.length).set(b);assert.equal(c.open(n,ptr,b.length),1);}
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/spell-notice-animation-native.json'),'utf8'));
const float=bits=>{const b=new ArrayBuffer(4);new Uint32Array(b)[0]=bits;return new Float32Array(b)[0];},state=templ=>Array.from({length:16},(_,n)=>c.notice_animation_state(n,templ)>>>0);
let frames=0;
for(const row of proof.rows){assert.equal(c.notice_animation_begin(row.script,float(row.rateBits)),1);assert.deepEqual(state(1),row.template,`template${row.script}/${row.rateBits}`);
 for(const f of row.frames){assert.equal(c.notice_animation_tick(),f.status,`status${row.script}/${row.rateBits}/${f.frame}`);assert.deepEqual(state(0),f.state,`state${row.script}/${row.rateBits}/${f.frame}`);++frames;}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'tests/cpp/th14-hud-resource-fixture.cpp','cpp/game/AnmVm.cpp','cpp/game/AnmInterpreter.cpp','cpp/game/AnmManager.cpp','cpp/game/AnmResource.cpp'];
writeFileSync(resolve(root,'docs/porting/th14-spell-notice-animation-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,timelines:proof.rows.length,frames,nativeExecutableSha256:proof.executableSha256,resourceSha256:proof.resourceSha256,wasmSha256:sha(bytes),scope:proof.scope+' Production opens original front/ascii and prepares all templates before copying the notice script. Direct VM updates isolate interpreter state from manager deletion; full notice delivery and actual GameSession manager retirement are separate proofs.',sources:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),tools:Object.fromEntries(['tools/th14-spell-notice-animation-native.py','tools/th14-spell-notice-animation-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');
console.log(`PASS ${proof.rows.length} original spell notice timelines / ${frames} exact interpreter states`);
