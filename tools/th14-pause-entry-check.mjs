import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/pause-entry-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-pause-entry-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-pause-entry-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'pause.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/pause-entry-native.json'),'utf8'));
for(const row of proof.entries){
 const script=row.kind==='game_over'?52:row.replay?130:129;assert.equal(c.run(script,0),1);
 assert.deepEqual(Array.from({length:c.binding_count()},(_,n)=>c.binding(n)),row.bindings.map(r=>r[1]));
 // Game-over music/audio delivery is handled by the application. Pause owns
 // its entry sound; result-entry music is outside this fixture.
 if(row.kind==='pause')assert.deepEqual(Array.from({length:c.sound_count()},(_,n)=>c.sound(n)),row.sounds);
 assert.equal(c.capture(),1);
}
for(const row of proof.factories){assert.equal(c.run(row.script,row.program),1);assert.deepEqual(Array.from({length:9},(_,n)=>c.value(row.script,n)>>>0),row.vm,JSON.stringify(row));}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,entryPaths:proof.entries.length,overlayFactoryCases:proof.factories.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),
 scope:'TH14 normal/replay pause and game-over capture bindings, pause entry sound, and native overlay factory layer/flags/position/rotation after one controlled ANM update. GPU capture, result music, score/ranking records, confirmation and replay-save transitions remain unverified.',
 sourceHashes:Object.fromEntries([fixture,'cpp/game/PauseMenu.cpp','cpp/game/PauseEnd.cpp','cpp/game/PauseMenu.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-pause-entry-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.entryPaths} pause/end entry paths, ${report.overlayFactoryCases} overlay factories.`);
