import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/score-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-score-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'score.wasm'),fixture='tests/cpp/th16-score-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/score-native.json'),'utf8'));
const hex=(p,n)=>Buffer.from(new Uint8Array(c.memory.buffer,p,n)).toString('hex');
assert.equal(hex(c.initialize_character(),0x5318),proof.initial);
for(const [index,r] of proof.cases.entries()){
 assert.equal(c.insert(r.difficulty,r.score,r.stage,r.continues,r.ratio,r.season),r.rank,JSON.stringify({index,...r,rows:undefined}));
 assert.equal(hex(c.rows(),60*32),r.rows,JSON.stringify({index,...r,rows:undefined}));
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-score-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,characterBytes:0x5318,insertions:proof.cases.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Complete own4493c0 character defaults, including all60 high-score rows and119 spell index/difficulty defaults, with memset controlled. Complete43e250 insertion with timestamp controlled and replay timing ratio supplied: unsigned comparison, equal-score placement,32-byte row shifts, retained byte15, byte stage/continue, name default, timestamp, slowdown and subseason. All60 rows compared after each insertion. Production accepts computed slowdown; real timing accumulation, disk codec, complete scorefile initialization, settings RNG and menu integration excluded.',sourceHashes:Object.fromEntries(['cpp/game/ScoreFile.cpp','cpp/game/ScoreFile.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS full TH16 character defaults and ${proof.cases.length} insertions`);
