import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/enemy-callbacks-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th16-enemy-callbacks-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-enemy-callbacks-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'callbacks.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/enemy-callbacks-native.json'),'utf8'));
for(const r of proof.cases){const p=c.allocate(Math.max(r.input.length,1)*4);new Uint32Array(c.memory.buffer,p,r.input.length).set(r.input);c.run(r.count,r.radiusBits,...r.playerBits,p);assert.deepEqual(Array.from({length:r.output.length},(_,n)=>c.value(n)>>>0),r.output,`list${r.n}`);c.release(p);}
for(const r of proof.selectors){assert.equal(c.selector(r.index,r.mode),0);assert.deepEqual([c.selector_word(0)>>>0,c.selector_word(1)>>>0],r.output);assert.equal(c.selector_word(2),r.index);}
for(const seed of proof.emptyResets)assert.equal(c.empty_reset(),0,`empty reset ${seed}`);
assert.equal(c.selector(2,0),-2);assert.equal(c.selector(-1,0),-2);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-enemy-callbacks-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,lists:proof.cases.length,selectors:proof.selectors.length,emptyLaserResets:proof.emptyResets.length,nativeExecutableSha256:proof.executableSha256,scope:'Full4252d0 linked-list proximity consumer without controlled internal functions: extra1 bullets strictly inside float32 squared radius switch to extra2, transform index8 and active mask0; zero/negative radius, exact edges, unordered NaN and infinity covered. Own4202b6 ECL632 selector for indices0/1 with argument resolver controlled; pointer represented by portable enum/index; production EnemyScriptServices routing exercised. Whole422550/4319e0 empty-list laser reset preserves all0x600 manager bytes across32 patterns; portable actual ECL545 routing preserves its empty manager. Live laser reset/cancellation, index2, ECL633 mode, actual ETEX programs following index8, complete frame and game excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,'cpp/game/EnemyCallbacks.cpp','cpp/game/EnemyCallbacks.hpp','cpp/game/EnemyCommands.hpp','cpp/game/EnemyScript.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} TH16 proximity lists / ${proof.selectors.length} callback selectors`);
