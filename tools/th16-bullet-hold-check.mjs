import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/bullet-hold-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-bullet-hold-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'hold.wasm'),fixture='tests/cpp/th16-bullet-hold-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/bullet-hold-native.json'),'utf8'));let frames=0;
function compare(expected,result,label){
 assert.equal(result,expected.result|0,`${label} result`);
 assert.deepEqual(Array.from({length:20},(_,n)=>c.value(n)>>>0),expected.output,`${label} state`);
 assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>c.event(n)),expected.events,`${label} deliveries`);
}
for(const [n,r] of proof.cases.entries()){
 // Retail413860 returns void; EAX after descriptor dispatch is incidental.
 compare({...r.initial,result:0},c.begin_case(...r.input),`case${n} initialize`);
 for(const [frame,f] of r.timeline.entries()){compare(f,c.step(),`case${n} frame${frame}`);++frames;}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-bullet-hold-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,initializers:proof.cases.length,frames,maximumObservedFieldError:0,nativeExecutableSha256:proof.executableSha256,scope:'Own413d1f initialization and full411e70 with own4162d0 offscreen hold, ETEX1 concurrency, same-frame continuation, retirement and rate clocks. Sprite17x36, ten edge/interior/exterior positions, eight angles, six durations, four mode flags, eight rates. D3DXVec2Normalize is a controlled float32 mathematical service; collision/ANM/retirement are controlled services. Other ETEX, GPU, full game and pixel equivalence excluded.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/BulletTh16.cpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`PASS ${proof.cases.length} own TH16 hold initializers / ${frames} full bullet frames; field error0`);
