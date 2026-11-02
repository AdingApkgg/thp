import assert from 'node:assert/strict';
import{readFileSync,writeFileSync}from'node:fs';
import{resolve}from'node:path';
import{WASI}from'node:wasi';
import{createHash}from'node:crypto';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/frame-rng-scope-nov02/counter-integrated-component'),sha=b=>createHash('sha256').update(b).digest('hex');
const raw=readFileSync(resolve(root,'artifacts/th14/frame-rng-scope-nov02/counter-restore/native.json')),native=JSON.parse(raw);assert.equal(native.actualOriginalWorkerCounterStoreExecuted,true);
assert.equal(sha(readFileSync(resolve(root,'tools/th14-rng-actor-counter-restore-native-nov02.py'))),native.toolSha256);
const rows=native.cases.filter(r=>r.rngReturns.length);assert.equal(rows.length,480);const results={};
for(const kind of ['candidate']){
 const dir=home,buildRaw=readFileSync(resolve(dir,'build.json')),build=JSON.parse(buildRaw),wasm=readFileSync(resolve(dir,'component.wasm'));assert.equal(sha(wasm),build.wasmSha256);
 for(const[name,digest]of Object.entries(build.sourceHashes))assert.equal(sha(readFileSync(resolve(root,name))),digest);
 const wasi=new WASI({version:'preview1'}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 let differences=0,counterCollisions=0;const mismatches=[];
 for(const[index,r]of rows.entries()){
  assert.equal(r.workerCounterRestoreDelivered,true);
  const pointer=c.stack_case(r.kind==='phased'?1:0,r.rate,r.seed,r.timer,r.prior),actual=Array.from(new Uint32Array(c.memory.buffer,pointer,11));
  const expected=[r.stackWord,1,r.result,...r.rng,...r.timerWords,...r.offsetWords,1];assert.deepEqual(actual.slice(1),expected.slice(1),`${kind}/${index} numeric behavior`);
  if(r.kind==='phased'){assert.equal(r.initialCalls,r.rng[1]);assert.equal(r.rngReturns.length,2);++counterCollisions;}
  if(actual[0]!==expected[0]){++differences;mismatches.push({index,kind:r.kind,actual:actual[0],expected:expected[0],counterBefore:r.initialCalls,counterAfter:r.rng[1]});}
 }
 assert.equal(counterCollisions,192);results[kind]={cases:480,differentStackWords:differences,counterCollisions,wasmSha256:build.wasmSha256,buildSha256:sha(buildRaw),mismatches};
}
assert.equal(results.candidate.differentStackWords,0);
const result={passed:true,originalInstructionCases:2016,activeRngComparisons:480,actualOriginalVisualCounterStoreExecuted:true,counterCollisions:192,results,nativeReportSha256:sha(raw),rootProductionChanged:true,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(home,'verified.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,nativeProfiles:2016,activeComparisons:480,candidateDifferentWords:0,counterCollisions:192}));
