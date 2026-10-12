import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/boss-wait-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-boss-wait-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/boss-wait-native.json'),'utf8')),env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'boss-wait.wasm'),fixture='tests/cpp/th16-boss-wait-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const r of proof.registrations){assert.equal(c.registration(...r.slice(0,4)),0);assert.deepEqual(Array.from({length:7},(_,i)=>c.value(i)>>>0),r.slice(4));}
for(const r of proof.lookups)assert.equal(c.lookup(...r.slice(0,3)),r[3],`lookup ${r.slice(0,3)}`);
for(const r of proof.waits)assert.equal(c.wait(...r.slice(0,2))>>>0,r[2],`wait ${r.slice(0,2)}`);
for(const op of [502,503,512,518,520])assert.equal(c.route(op),1);
for(const r of proof.flagRows){assert.equal(c.flags(r.op,r.flags,r.bits),0);assert.equal(c.value(0)>>>0,r.after);assert.equal(c.visibility_count(),r.visibility.length);r.visibility.forEach((v,j)=>assert.deepEqual([c.visibility_value(j,0),c.visibility_value(j,1)],v));}
for(const r of proof.spellPracticeReads)assert.equal(c.spell_practice(r[0],r[1])>>>0,r[2],`spell-practice getter ${r.slice(0,2)}`);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-boss-wait-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,registrations:proof.registrations.length,lookups:proof.lookups.length,waits:proof.waits.length,flagCases:proof.flagRows.length,spellPracticeReads:proof.spellPracticeReads.length,scope:proof.scope+' C++ comparisons execute production EnemyScriptServices command routing for registration/wait/flags, plus actual EnemyManager lookup. Constructor ID fragment is a native observation only; full constructor, resource lifecycle and frame flags remain outside coverage.',nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/EnemyManager.cpp','cpp/game/EnemyManager.hpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyState.cpp','cpp/game/EnemyCommands.hpp','cpp/game/EclRoutes.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),referenceCrossCheck:'https://github.com/exphp-share/th-re-data/blob/master/data/th16.v1.00a/type-structs-own.json'},null,2)+'\n');
console.log(`PASS ${proof.registrations.length} TH16 boss registrations, ${proof.lookups.length} lookups, ${proof.waits.length} waits`);
