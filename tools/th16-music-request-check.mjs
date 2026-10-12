import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/music-request-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-music-request-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/music-request-native.json'),'utf8')),env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'music-request.wasm'),fixture='tests/cpp/th16-music-request-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th16/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th16.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);assert.equal(c.begin(),1);
for(const row of proof.table)for(let boss=0;boss<2;++boss)assert.equal(c.cue(row.stage,boss),row.cues[boss]);
let cases=0;
for(const row of proof.rows.filter(r=>r.stop===0&&r.practiceMatch===0)){
 assert.equal(c.request(row.stage,row.id,!!row.existing),1,`request ${row.stage}/${row.id}`);
 const audio=row.events.find(e=>e[0]==='audio'),front=row.events.find(e=>e[0]==='front');assert.equal(audio[1],2);assert.equal(front[3],0);
 assert.deepEqual(Array.from({length:11},(_,i)=>c.value(i)),[1,audio[2]?8:11,row.stage,1,front[1],front[2]|0,1,+!!row.existing,37,123,456]);
 assert.equal(row.dialogueAfter,row.existing);assert.equal(row.unlocks[row.cues?.[audio[2]]??proof.table[row.stage-1].cues[audio[2]]],1);++cases;
}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const r of proof.logos){assert.equal(c.logo(r.mode,r.flags),0);if(r.events.length){assert.ok(c.value(3)>=1);assert.deepEqual([c.value(4),c.value(5)],[r.events[0][1],r.events[0][2]|0]);}else assert.equal(c.value(3),0);}
writeFileSync(resolve(root,'docs/porting/th16-music-request-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,nativeCases:proof.rows.length,portableOrdinaryRequestCases:cases,logoCases:proof.logos.length,stageCues:proof.table,scope:proof.scope+' Portable comparisons cover ordinary requests only: event selector, descriptor cue, actual original front resource creation request/first update, retained dialogue object/activity/release and unchanged stage section/frame. Config-bit4 stop command and spell-practice suppression are native observations only, pending production integration. Front render mode17, native animation factory internals, music playback/unlock persistence and ECL cancellation are excluded.',nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),archiveSha256:sha(dat),sourceHashes:Object.fromEntries(['cpp/game/GameBattle.cpp','cpp/game/EnemyManager.cpp','cpp/game/MusicCatalog.hpp','cpp/game/EnemyAnimations.cpp','cpp/game/EnemyAnimations.hpp','cpp/game/EnemyScript.cpp','cpp/game/EnemyCommands.hpp','cpp/game/AnmManager.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolHashes:Object.fromEntries(['tools/th16-music-request-check.mjs','tools/th16-music-request-native.py'].map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
console.log(`PASS ${cases} ordinary TH16 music requests, ${proof.rows.length} native branch observations, 14 descriptor cues`);
