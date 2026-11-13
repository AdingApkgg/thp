// Reuse unchanged retail input/result records; compile the current component.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';

const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const out=resolve(root,'artifacts/th14/ordinary-difficulties-nov14/player-collision-current-recheck');
assert.ok(!existsSync(out));mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
const prior=JSON.parse(readFileSync(resolve(root,'docs/porting/th14-player-bullet-collision-verified.json')));
for(const [name,digest]of Object.entries(prior.toolHashes))assert.equal(sha(readFileSync(resolve(root,name))),digest,name);
const nativePath=resolve(root,'artifacts/th14/player-bullet-collision-native.json');
const native=JSON.parse(readFileSync(nativePath));
assert.equal(native.cases.length,prior.cases);assert.equal(prior.cases,10800);
assert.equal(native.executableSha256,prior.nativeExecutableSha256);
const fixture='tests/cpp/th14-player-bullet-collision-fixture.cpp';
assert.equal(sha(readFileSync(resolve(rt,fixture))),prior.sourceHashes[fixture]);
const wasm=resolve(out,'collision.wasm');
execFileSync(resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),
 ['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
  '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,'cpp/game/PlayerCollision.cpp','-o',wasm],
 {cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},windowsHide:true,stdio:'pipe'});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const f32=new Float32Array(1),u32=new Uint32Array(f32.buffer);
const toFloat=bits=>{u32[0]=bits;return f32[0];};
const mismatches=[];
for(const [index,row]of native.cases.entries()){
 const input=row.input.map((v,n)=>n>=1&&n<=8?toFloat(v):v);
 const actual=instance.exports.test(...input),expected=row.result[0]|(row.result[1]<<8);
 if(actual!==expected)mismatches.push({index,inputBits:row.input,expected,actual});
}
const sources=[fixture,'cpp/game/PlayerCollision.hpp','cpp/game/PlayerCollision.cpp'];
const q={passed:mismatches.length===0,cases:native.cases.length,mismatchCount:mismatches.length,
 firstMismatches:mismatches.slice(0,12),retailCaseFileSha256:sha(readFileSync(nativePath)),
 priorProofSha256:sha(readFileSync(resolve(root,'docs/porting/th14-player-bullet-collision-verified.json'))),
 unchangedRetailGeneratorHashesVerified:true,actualCurrentComponentCompiled:true,
 wasmSha256:sha(bytes),priorWasmSha256:prior.wasmSha256,wasmUnchanged:sha(bytes)===prior.wasmSha256,
 sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolSha256:sha(readFileSync(import.meta.filename)),nativeProcessLaunched:false,
 currentSceneExtraGrazeExplained:false,gameLogicChanged:false,completeGame:false};
writeFileSync(resolve(out,'report.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify(q));
if(!q.passed)process.exitCode=1;
