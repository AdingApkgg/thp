import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,process.argv[2]);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const nativeBytes=readFileSync(resolve(home,'native.json')),native=JSON.parse(nativeBytes);
const buildBytes=readFileSync(resolve(home,'build.json')),build=JSON.parse(buildBytes);
for(const [name,row]of Object.entries(build.bindings)){
 const raw=readFileSync(resolve(root,name));assert.equal(raw.length,row.bytes);assert.equal(sha(raw),row.sha256,name);
}
const wasm=readFileSync(resolve(home,'fixture.wasm'));
assert.equal(sha(wasm),build.wasmSha256);
const module=await WebAssembly.compile(wasm);
assert(WebAssembly.Module.imports(module).every(row=>row.module==='wasi_snapshot_preview1'));
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const instance=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
const phases=['before_read','seed_read','counter_committed','before_store','seed_written'];
const out=(ptr,n)=>Array.from(new Uint32Array(c.memory.buffer,ptr,n));
let cases=0,wrongBoundaryRejected=0,beforeReadProductionPairs=0;
for(const row of native.profiles){
 const point=phases.indexOf(row.phase);assert(point>=0);
 const actual=out(c.rng_case(row.bits,row.seed,row.restore,row.calls,point,row.locking),10);
 assert.deepEqual(actual,[row.result,...row.final,...row.before,...row.afterWorker],JSON.stringify(row));
 ++cases;
 if(row.phase==='before_read'){
  const atomic=out(c.rng_atomic_case(row.bits,row.restore,row.calls),4);
  assert.deepEqual(atomic,[row.result,...row.final]);++beforeReadProductionPairs;
 }
 // Delivering the same intervention before the RNG read is an intentionally
 // wrong model for the native before-store cases. Keep every disagreement.
 if(row.phase==='before_store'){
  const wrong=out(c.rng_case(row.bits,row.seed,row.restore,row.calls,0,row.locking),4);
  if(wrong.some((v,i)=>v!==[row.result,...row.final][i]))++wrongBoundaryRejected;
 }
}
assert.deepEqual(out(c.scope_lifetime_case(),4),[10,5,1,8]);
assert.deepEqual(out(c.scope_failure_case(),3),[2,1,1]);
assert.deepEqual(out(c.scope_reentry_case(),3),[5,3,1]);
assert.equal(cases,800);assert.equal(beforeReadProductionPairs,160);assert(wrongBoundaryRejected>0);
const report={verifiedFiniteInstructionStoreComponent:true,scopedObserverLifetimeFailureAndReentryControlsPassed:true,cases,beforeReadProductionPairs,wrongBeforeReadInsteadOfBeforeStoreRejected:wrongBoundaryRejected,nativeReportSha256:sha(nativeBytes),candidateBuildSha256:sha(buildBytes),wasmSha256:sha(wasm),toolSha256:sha(readFileSync(import.meta.filename)),productionEngineChanged:false,liveNativeControlledScheduleAccepted:false,historical36826FailureClosed:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(home,'component-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
