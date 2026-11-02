// Replay the recorded debugger delivery order into an isolated synthetic heap.
import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/replay-candidates-second-nov03/crt-common-free-original/main'),large=resolve(root,'artifacts/th14/replay-candidates-second-nov03/process-heap-model-large'),base=resolve(root,'artifacts/th14/replay-candidates-second-nov03/process-heap-model-v3'),sha=x=>createHash('sha256').update(x).digest('hex');
assert(process.argv.slice(2).every(x=>x==='--check')&&process.argv.slice(2).length<=1);
const build=JSON.parse(read(resolve(large,'build.json'))),baseBuild=JSON.parse(read(resolve(base,'build.json'))),largeBytes=read(resolve(large,'large.wasm')),baseBytes=read(resolve(base,'candidate.wasm'));
assert.equal(sha(largeBytes),build.wasmSha256);assert.equal(sha(baseBytes),baseBuild.variants.find(x=>x.name==='candidate').wasmSha256);assert.equal(sha(read(resolve(root,'tools/th14-process-heap-model-nov03.cpp'))),build.baseSourceSha256);assert.equal(sha(read(resolve(large,'large.cpp'))),build.derivedSourceSha256);
const instantiate=async bytes=>{const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);instance.exports.heap_model_reset(0x20000000,0x10000000);return instance.exports;};
// Capacity extension must not alter model choices on a bounded control trace.
const smallControl=await instantiate(baseBytes),largeControl=await instantiate(largeBytes),live=[];
for(let i=0;i<600;i++){
 if(live.length&&i%3===0){const index=(i*17)%live.length,[a,b]=live.splice(index,1)[0];assert.equal(smallControl.heap_model_free(a),1);assert.equal(largeControl.heap_model_free(b),1);}
 else if(live.length<80){const size=1+(i*127)%1500,a=smallControl.heap_model_alloc(size)>>>0,b=largeControl.heap_model_alloc(size)>>>0;assert(a&&a===b);live.push([a,b]);}
}
assert.equal(smallControl.heap_model_ok(),1);assert.equal(largeControl.heap_model_ok(),1);
const proofRaw=read(resolve(root,'docs/porting/th14-crt-common-free-trace-nov03.json')),proof=JSON.parse(proofRaw),order=JSON.parse(read(resolve(root,'docs/porting/th14-crt-cross-thread-order-nov03.json'))),raw=read(resolve(home,'native/crt-heap-events.jsonl')),events=raw.toString().trim().split('\n').map(JSON.parse);
assert(proof.verifiedFiniteOriginalBootCrtHeapTrace&&order.verifiedRecordedDebugDeliveryOrderClassification);assert.equal(sha(raw),proof.eventLogSha256);assert.equal(sha(raw),order.eventLogSha256);assert.equal(sha(proofRaw),order.proofSha256);assert.equal(events.length,proof.crtAllocationReturns+proof.crtFreeEntries+proof.enemyAllocationReturns);
const c=await instantiate(largeBytes),active=new Map(),nativeLast=new Map(),modelLast=new Map(),modelByToken=new Map(),predictions=new Map();
let allocations=0,frees=0,unknownFrees=0,nullFrees=0,enemy=0,enemyMatched=0,enemyReuse=0,enemyRelative=0,reuse=0,firstNativeEnemy=null,firstModelEnemy=null;
for(const event of events){
 if(event.event==='crt-heap-allocation-return'){
  assert(event.address&&event.requestedBytes>0&&!active.has(event.address));const token=++allocations,prior=nativeLast.get(event.address)??null,address=c.heap_model_alloc(event.requestedBytes)>>>0;assert(address);const modelPrior=modelLast.get(address)??null,reuseEqual=prior===modelPrior;if(reuseEqual)reuse++;
  active.set(event.address,token);nativeLast.set(event.address,token);modelLast.set(address,token);modelByToken.set(token,address);predictions.set(token,{reuseEqual});
 }else if(event.event==='crt-free-entry'){
  if(!event.address){nullFrees++;continue;}const token=active.get(event.address);if(token===undefined){unknownFrees++;continue;}assert.equal(c.heap_model_free(modelByToken.get(token)),1);active.delete(event.address);frees++;
 }else{
  assert.equal(event.event,'enemy-allocation-return');enemy++;const token=active.get(event.address);if(token===undefined)continue;enemyMatched++;const modelAddress=modelByToken.get(token);if(firstNativeEnemy===null){firstNativeEnemy=event.address;firstModelEnemy=modelAddress;}if(predictions.get(token).reuseEqual)enemyReuse++;if(event.address-firstNativeEnemy===modelAddress-firstModelEnemy)enemyRelative++;
 }
}
assert.equal(allocations,proof.crtAllocationReturns);assert.equal(frees+unknownFrees+nullFrees,proof.crtFreeEntries);assert.equal(enemy,proof.enemyAllocationReturns);assert.equal(frees,order.counts.matchedFreeEntries);assert.equal(c.heap_model_ok(),1);
const result={verifiedRecordedDeliveryOrderModelExperiment:true,callbacks:proof.callbacks,allocations,matchedNonNullFreeEntries:frees,unmatchedNonNullFreeEntries:unknownFrees,nullFreeEntries:nullFrees,allAllocationReuseIdentityMatches:reuse,enemyReturns:enemy,enemyReturnsMatchingTrackedAllocation:enemyMatched,enemyReuseIdentityMatches:enemyReuse,enemyRelativePositionMatches:enemyRelative,capacityExtensionControlOperations:600,capacityExtensionControlMatched:true,modelReceivesOnlySizesAndObservedLifetimeOrder:true,actualOriginalAddressesProvidedToModel:false,debugDeliveryOrderAssumedMemoryOrderForExperiment:true,freeSuccessAssumedForExperiment:true,earlierActivityAndDirectOsCallsNotModeled:true,originalHeapHistoryReconstructed:false,productionIntegrated:false,completeGame:false,nativeEquivalent:false,eventLogSha256:sha(raw),traceProofSha256:sha(proofRaw),largeWasmSha256:sha(largeBytes),toolSha256:sha(read(new URL(import.meta.url))),scope:'Finite synthetic model experiment using debugger event delivery order. The ordering across threads and free success are assumptions, not established original memory order. Loader history before attach and direct OS calls are omitted; original addresses are used only for identity and relative comparisons and are not provided to the candidate.'};
const out=resolve(root,'docs/porting/th14-crt-boot-model-trace-nov03.json'),encoded=JSON.stringify(result,null,2)+'\n';if(process.argv.includes('--check'))assert.equal(read(out,'utf8'),encoded);else{assert(!existsSync(out));write(out,encoded,{flag:'wx'});}console.log(JSON.stringify(result));
