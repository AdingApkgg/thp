import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-anm-setters-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-enemy-anm-setters-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'enemy-anm-setters.wasm'),fixture='tests/cpp/th16-enemy-anm-setters-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-anm-setters-native.json'),'utf8'));
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.run_case(r.op,r.slot,Number(r.available),r.flags,...r.args.slice(1)),0);
 assert.deepEqual(Array.from({length:24},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify({index,...r}));
}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const r of proof.sounds){assert.equal(c.sound_case(r.id,r.x,1),0);assert.deepEqual([c.sound_value(0)>>>0,c.sound_value(1)>>>0],r.output);assert.equal(c.sound_case(r.id,r.x,0),-2);}
writeFileSync(resolve(root,'docs/porting/th16-enemy-anm-setters-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,soundCases:proof.sounds.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Full own4233a0 branches319/325/327/329/331/335/337 with controlled argument resolvers and registry lookup. Rotation, scale and velocity, byte RGB/alpha writes, blend mode, unsigned16-slot guards and stale handle clearing compared through actual EnemyScriptServices dispatch. Own421668 sound516 positional request with controlled sound delivery; actual EnemyManager and missing-service rejection exercised. Interpolation branches, layer consumer, VM update, resource creation and rendering excluded.',sourceHashes:Object.fromEntries(['cpp/game/EnemyAnimations.cpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyManager.cpp','cpp/game/GameBattle.cpp','cpp/game/GameBattle.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 enemy ANM setter cases`);
