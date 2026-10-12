import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/bullet-appearance-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-bullet-appearance-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'appearance.wasm'),fixture='tests/cpp/th16-bullet-appearance-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/bullet-appearance-native.json'),'utf8'));
for(const [n,r] of proof.cases.entries()){assert.equal(c.run_case(...r.input),0,`case${n}`);assert.deepEqual(Array.from({length:11},(_,n)=>c.value(n)>>>0),r.output,`case${n} ${r.input}`);assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>Array.from({length:6},(_,f)=>c.event_word(n,f)>>>0)),r.events,`case${n} events`);}
const bits=f=>new Uint32Array(new Float32Array([f]).buffer)[0];let production=0;
for(let style=0;style<44;style++)for(let color=0;color<16;color++)for(const fast of [0,0x8000]){const packed=color|fast;assert.equal(c.production_case(style,packed),0);const r=proof.cases.find(r=>r.input[0]===style&&(r.input[1]&0x7fff)===color&&r.events.length);assert.ok(r);assert.equal(c.production_word(0)>>>0,r.events[1][1]);assert.deepEqual(Array.from({length:10},(_,n)=>c.production_word(n+1)>>>0),[fast?2:0,0x40000,1,9,bits(7),bits(11),bits(13),1,1,3]);production++;}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-bullet-appearance-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,productionBindings:production,nativeExecutableSha256:proof.executableSha256,scope:'Whole413860 ETEX512,44 styles/16 colors, packed flags8000/10000, active/concurrent guards, scalar metadata/cancel family/origin flags and reset-bind-secondary service order. Native VM initialization/resource binding controlled; actual4173c0 executes with no callback. Portable production manager checked against blank322-script catalog for first update, callback binding, origin, interruption, preserved XYZ/layer/state/program. Full VM reset/binding equality with real resources, secondary VM lifecycle, nonzero interrupt callbacks, pixels and complete game excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/BulletTh16.cpp','cpp/game/BulletTh16.hpp','cpp/game/BulletManager.cpp','cpp/game/BulletManager.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} TH16 appearance replacements / ${production} production bindings`);
