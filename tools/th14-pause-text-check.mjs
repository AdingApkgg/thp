import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/pause-text-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
if(!process.argv.includes('--skip-native'))nativePython('tools/th14-pause-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-pause-text-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'pause-text.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/pause-text-native.json'),'utf8'));assert.equal(native.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const copy=hex=>{const b=Buffer.from(hex,'hex'),p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const catalog=native.catalog.map(r=>r?copy(r.header):0),records=copy(native.records),bits=x=>{const b=Buffer.alloc(4);b.writeFloatLE(x);return b.readUInt32LE();};
const states={9:9,10:10,15:14,17:16,18:17,19:18,26:23,27:24,28:25};let requests=0;
// Save decoding is independent of the draw state. Load the real replay catalog
// once, then preserve it while resetting just the menu fields for each layout.
for(const [i,p] of catalog.entries())assert.equal(c.entry(i,p),1,`replay ${i}`);
for(const [ordinal,row] of native.rows.entries()){
 c.setup(states[row.state],row.timer,row.selected,row.length,row.glyph,row.unranked,row.selection,row.difficulty,row.stage,row.credits,copy(row.header),records);
 assert.equal(c.queue(),row.requests.length,`layout ${ordinal} count`);
 for(const [i,r] of row.requests.entries()){const p=c.bytes(i),mem=new Uint8Array(c.memory.buffer);assert.equal(Buffer.from(mem.subarray(p,mem.indexOf(0,p))).toString('hex'),r.text,`layout ${ordinal}, request ${i}: text`);assert.deepEqual(Array.from({length:8},(_,k)=>c.value(i,k)>>>0),[...r.position.map(bits),r.color,r.shadow,r.font,...r.scale.map(bits)],`layout ${ordinal}, request ${i}: style`);++requests;}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=[`runtimes/th12/th12_web/${fixture}`,'runtimes/th12/th12_web/cpp/game/PauseText.cpp','tools/th14-pause-text-native.py','tools/th14-pause-text-check.mjs'];
writeFileSync(resolve(root,'docs/porting/th14-pause-text-verified.json'),JSON.stringify({passed:true,completeGame:false,nativeEquivalent:false,layouts:native.rows.length,requests,nativeExecutableSha256:native.executableSha256,wasmSha256:sha(bytes),scope:native.scope+' Production PauseMenu::queue_ascii compares every byte and eight position/style words. ReplayRecorder compresses/encrypts and Replay parses catalog entries before drawing.',sources:Object.fromEntries(sources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${native.rows.length} Pause layouts / ${requests} ASCII requests exact`);
