import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/pause-text-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-pause-text-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'pause-text.wasm'),fixture='tests/cpp/th16-pause-entry-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/pause-text-native.json'),'utf8'));
const string=p=>{const b=new Uint8Array(c.memory.buffer);return Buffer.from(b.subarray(p,b.indexOf(0,p))).toString('latin1');};
for(const [index,r] of proof.cases.entries()){
 c.text_case(r.sub,r.rank,r.selected,r.length,r.unranked,r.dated,r.credits);
 assert.deepEqual(Array.from({length:c.text_count()},(_,n)=>({text:string(c.text_string(n)),words:Array.from({length:4},(_,f)=>c.text_word(n,f)>>>0)})),r.requests,JSON.stringify({index,...r,requests:undefined}));
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-pause-text-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Own43edc0 normal game-over draw requests,43ec10 ranking and43e730 name/91-key grid.408260 formatting and delivery controlled; localtime supplies1970-01-02. Compare emitted Latin1 strings, x/y/z float bits and colors for ranked/unranked, empty/full names, default/dated score rows, selected rank/key and credits. Font atlas glyphs, shadow pixels, capture tint, replay/practice display and native graphics excluded.',sourceHashes:Object.fromEntries(['cpp/game/PauseText.cpp','cpp/game/PauseMenu.hpp','cpp/game/ScoreFile.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');console.log(`PASS ${proof.cases.length} own TH16 game-over ASCII request cases`);
