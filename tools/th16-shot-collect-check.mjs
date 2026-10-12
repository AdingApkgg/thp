import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-collect-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-collect-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-collect-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'collect.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-collect-native.json'),'utf8'));
for(const [index,r] of proof.rows.entries()){
 const why=JSON.stringify({index,seed:r.seed,cap:r.cap,advanced:r.advanced});assert.equal(c.begin(r.seed,r.cap,r.advanced),1,why);
 assert.deepEqual(Array.from({length:5},(_,k)=>c.value(k)>>>0),r.output,why);
 for(const [id,words] of Object.entries(r.areas))assert.deepEqual(Array.from({length:37},(_,k)=>c.area(+id,k)>>>0),words,why+` area${id}`);
 assert.deepEqual(Array.from({length:c.count()},(_,n)=>Array.from({length:3},(_,k)=>c.event(n,k)>>>0)),r.events,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-collect-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Full445a30 executes, raw256 records with seeded indices1/2/256. Frame guard preserves outputs; active Bomb/negative initial damage; timer equality/period/signed remainder; circular direct geometry; rectangle geometry branch requests; stamp suppression/updates; Bomb bit4; probe skipping hit and total accumulation; hit mutates damage before total; signed wrapping totals/result; capacity retire, cap clamp and43e080 score request. Rectangle/circle-rectangle primitives, hit callback, Bomb virtual and score are controlled boundaries. All area words and ordered services exact. Native invalid division inputs explicitly unsupported; complete geometry, actual hit callbacks/Bomb, natural gameplay and full game excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-collect-native.py','tools/th16-shot-collect-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 complete damage collections.`);
