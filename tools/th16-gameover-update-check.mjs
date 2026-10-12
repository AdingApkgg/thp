import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/gameover-update-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-gameover-update-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'gameover-update.wasm'),fixture='tests/cpp/th16-pause-entry-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/gameover-update-native.json'),'utf8'));
const memory=(p,n)=>new Uint8Array(c.memory.buffer,p,n);
for(const [index,r] of proof.cases.entries()){
 const label=JSON.stringify({index,...r,rows:undefined});
 assert.equal(c.end_case(r.selection,r.difficulty,r.score,r.continues,r.remaining,r.sub,r.clock,r.rate,r.last,r.selected,r.length,r.pressed,r.repeat),1,label);
 assert.deepEqual(Array.from({length:48},(_,n)=>c.end_word(n)>>>0),r.output,label);
 assert.deepEqual(Array.from({length:c.sound_count()},(_,n)=>c.sound(n)),r.sounds,label);
 assert.deepEqual(Array.from({length:c.binding_count()},(_,n)=>c.binding(n,1)),r.bindings,label);
 assert.equal(Buffer.from(memory(c.end_rows(),60*32)).toString('hex'),r.rows,label);
 assert.deepEqual(Array.from(memory(c.end_last_name(),9)),r.lastName,label);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-gameover-update-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own43e5f0/43f980 normal game-over score/name branches, including complete43f7e0 with43e250 ranking and insertion, ranked state15 input and finish, unranked160 choice creation and disabled-continue/replay rows. Full score character defaults supplied from independently verified4493c0. Timestamp and replay ratio1 controlled; repeat predicate, absent ANM children, visibility, overlay factory and immediate ANM update controlled. Compare both clocks, selection/cursor, disabled rows, all60 high-score rows, name editing, stored previous name, script requests, pending labels and sounds. HUD high/current score globals, native ANM/rendering, practice/clear branches, subsequent choices, saving and complete game excluded.',sourceHashes:Object.fromEntries(['cpp/game/PauseMenu.cpp','cpp/game/PauseMenu.hpp','cpp/game/PauseEnd.cpp','cpp/game/MenuCursor.cpp','cpp/game/ScoreFile.cpp','cpp/game/ScoreFile.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');console.log(`PASS ${proof.cases.length} own TH16 game-over score/name updates`);
