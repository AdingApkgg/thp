import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-random-movement-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-enemy-random-movement-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'movement.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16','tests/cpp/th16-enemy-random-movement-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-random-movement-native.json'),'utf8'));
const put=values=>{const p=c.allocate(Math.max(values.length,7)*4);new Uint32Array(c.memory.buffer,p,Math.max(values.length,7)).fill(0);new Uint32Array(c.memory.buffer,p,values.length).set(values);return p;};
const actual=()=>Array.from({length:53},(_,i)=>c.value(i)>>>0);
const interp=()=>Array.from({length:4},(_,n)=>Array.from({length:11},(_,i)=>c.interpolation_value(n,i)>>>0));
const bands=()=>Array.from({length:2},(_,n)=>Array.from({length:19},(_,i)=>c.position_value(n,i)>>>0));
for(const [index,r] of proof.cases.entries()){
 const p=put(r.initial),a=put(r.args);c.initialize(p,r.rate);c.random_setup(r.op,r.seed,r.calls,r.playerX,r.speedMode);assert.equal(c.command(r.op,a),0);
 assert.deepEqual(actual(),r.configuredState,`setter ${index}`);assert.deepEqual(interp(),r.configured,`bands ${index}`);assert.deepEqual([c.random_word(0)>>>0,c.random_word(1)>>>0],r.random,`rng ${index}`);
 for(const [f,v] of r.frames.entries()){assert.equal(c.tick()>>>0,v.status,`frame ${index}/${f}`);assert.deepEqual(actual(),v.result,`state ${index}/${f}`);assert.deepEqual(interp(),v.interpolation,`bands ${index}/${f}`);}c.release(p);c.release(a);
}
const paths=['cpp/game/EnemyTh16Movement.cpp','cpp/game/EnemyState.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyAnimations.cpp'];
const report={passed:true,title:16,completeGame:false,executableSha256:proof.executableSha256,commands:proof.cases.length,frames:proof.cases.reduce((n,r)=>n+r.frames.length,0),scope:'Own41ff77..420241 ECL412/413 random movement with actual native RNG and normalization, followed by eight frames of complete41bb50 movement with ANM lookup controlled. Bounds/player bias, scalar band initialization, persisting speed mode, seed and wrapping draw count compared. Finite inputs, modes0/4/7 and selected prior speed modes; renderer and full enemy lifecycle excluded.',sources:Object.fromEntries(paths.map(p=>[p,createHash('sha256').update(readFileSync(resolve(rt,p))).digest('hex')]))};
writeFileSync(resolve(root,'docs/porting/th16-enemy-random-movement-verified.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS: TH16 movement',JSON.stringify(report));
