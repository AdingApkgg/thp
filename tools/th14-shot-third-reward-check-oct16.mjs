// Compile the real production consumer and compare every word/action to original code.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const [label]=process.argv.slice(2);assert(['before','after'].includes(label)&&process.argv.length===3);
const out=resolve(root,'artifacts/th14/shot-third-reward-check-oct16',label);assert(!existsSync(out));mkdirSync(out,{recursive:true});
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex');
const proofBytes=read(resolve(root,'artifacts/th14/shot-third-reward-native-oct16.json')),proof=JSON.parse(proofBytes);
assert.equal(proof.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
assert(proof.originalCodeUnmodified&&proof.itemPoolsDeclaredFull);assert.equal(proof.rows.length,1920);
assert.equal(proof.toolSha256,sha(read(resolve(root,'tools/th14-shot-third-reward-native-oct16.py'))));
const fixture='tests/cpp/th14-shot-third-reward-fixture.cpp',wasm=resolve(out,'rewards.wasm');
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
execFileSync(compiler,['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,'cpp/game/ShotTh14.cpp','-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},windowsHide:true,stdio:'inherit'});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=read(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const differences=[];let emitted=0;
for(const [i,row] of proof.rows.entries()){
 assert.equal(c.run(row.power,row.plain,row.focused,row.third,row.seed),1);
 const actual=Array.from({length:6},(_,j)=>c.value(j)>>>0);
 const requests=Array.from({length:c.count()},(_,n)=>Array.from({length:6},(_,j)=>c.request(n,j)>>>0));emitted+=requests.length;
 if(JSON.stringify(actual)!==JSON.stringify(row.result)||JSON.stringify(requests)!==JSON.stringify(row.requests))differences.push({index:i,input:{power:row.power,plain:row.plain,focused:row.focused,third:row.third,seed:row.seed},actual,expected:row.result,actualRequests:requests,expectedRequests:row.requests});
}
const oldBytes=read(resolve(root,'artifacts/th14/shot-rewards-native.json')),old=JSON.parse(oldBytes);assert.equal(old.rows.length,1440);
for(const row of old.rows){assert.equal(c.run(row.power,row.plain,row.focused,0,row.seed),1);assert.deepEqual([c.value(0)>>>0,c.value(1)>>>0,c.value(3)>>>0,c.value(4)>>>0,c.value(5)>>>0],row.result);assert.equal(c.count(),row.requests.length);for(const[n,r]of row.requests.entries())assert.deepEqual(Array.from({length:6},(_,j)=>c.request(n,j)>>>0),r);}
const sourceHashes=Object.fromEntries([fixture,'cpp/game/ShotTh14.cpp','cpp/game/ShotManager.hpp'].map(n=>[n,sha(read(resolve(rt,n)))]));
writeFileSync(resolve(out,'all-differences.json'),JSON.stringify(differences,null,2)+'\n',{flag:'wx'});
const report={label,passed:differences.length===0,nativeCases:proof.rows.length,thirdAtLeast100Cases:960,differentCases:differences.length,actualAllocationAttempts:emitted,expectedAllocationAttempts:proof.rows.reduce((n,r)=>n+r.requests.length,0),oldImmutableRewardCases:1440,oldImmutableRewardCasesPassed:true,nativeProofSha256:sha(proofBytes),oldNativeProofSha256:sha(oldBytes),wasmSha256:sha(bytes),sourceHashes,toolSha256:sha(read(import.meta.filename)),originalCodeUnmodified:true,actualGraphicsOrAudio:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(out,'receipt.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));
if(label==='before')assert.equal(differences.length,960,'Only positive third-counter cases should fail');else assert.equal(differences.length,0);
