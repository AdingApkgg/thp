import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/options-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th14-options-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-options-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/options-native.json'),'utf8'));
let previousSlot=-1;
for(const [index,r] of proof.rows.entries()){
 if(previousSlot!==r.slot){const data=readFileSync(resolve(root,'artifacts/archive-differential/th14-bBPoO0',`pl0${r.slot>>1}${'ab'[r.slot%2]}.sht`)),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open(p,data.length),1);previousSlot=r.slot;}
 const why=JSON.stringify({index,...r});assert.equal(c.begin(r.slot,r.oldCount,r.power,r.focus),1,why);
 assert.deepEqual([c.value(0),c.value(1)].map(v=>v>>>0),r.result,why);
 assert.deepEqual(Array.from({length:8},(_,i)=>Array.from({length:11},(_,k)=>c.option(i,k)>>>0)),r.options,why);
 assert.deepEqual(Array.from({length:c.creations()},(_,n)=>c.created_script(n)),r.events.filter(e=>e[0]==='create').map(e=>e[1]),why);
 const actual=[];for(let aux=1;aux>=0;aux--)for(let i=0;i<8;i++)if(c.script(i,aux)>=0)actual.push([0,1,2].map(k=>c.animation(i,aux,k)>>>0));
 assert.deepEqual(actual,r.animations,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-options-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,resources:proof.resources,wasmSha256:sha(bytes),scope:'Retail 44f970 versus production PlayerMotion on six original SHT formations. Controlled old option count with empty previous animation handles; power thresholds, focused/unfocused coordinates, integer SSE conversion, count/angle, option state/index/snap, creation order/script, initial origin/layer/y. ANM allocation/binding/update/lookup/interrupt are boundaries; actual resource animation evolution, existing animation family deletion, option movement and complete player lifecycle are separate.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerMotion.cpp','cpp/game/PlayerMotion.hpp','cpp/game/ShtResource.cpp','cpp/game/AnmManager.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-options-native.py','tools/th14-options-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native option rebuild cases on six retail SHTs.`);
