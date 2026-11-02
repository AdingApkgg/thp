// Compare free-entry and observed successful-free-return orders on one trace.
import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/replay-candidates-second-nov03/heap-free-return-original/main'),M=resolve(R,'artifacts/th14/replay-candidates-second-nov03/process-heap-model-large'),sha=x=>createHash('sha256').update(x).digest('hex');assert(process.argv.slice(2).every(x=>x==='--check')&&process.argv.slice(2).length<=1);
const proofRaw=read(resolve(R,'docs/porting/th14-heap-free-return-trace-nov03.json')),proof=JSON.parse(proofRaw),raw=read(resolve(H,'native/crt-heap-events.jsonl')),events=raw.toString().trim().split('\n').map(JSON.parse),build=JSON.parse(read(resolve(M,'build.json'))),wasm=read(resolve(M,'large.wasm'));assert(proof.verifiedFiniteOriginalHeapFreeReturnTrace&&proof.debugExceptions===0&&proof.pendingNonNullFreeReturns===0&&!proof.counts.failedFreeReturns);assert.equal(sha(raw),proof.eventLogSha256);assert.equal(sha(wasm),build.wasmSha256);assert.equal(sha(read(resolve(R,'tools/th14-process-heap-model-nov03.cpp'))),build.baseSourceSha256);
async function model(){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);instance.exports.heap_model_reset(0x20000000,0x10000000);return instance.exports;}
const results=[];
for(const mode of ['entry','successful-return']){
 const c=await model(),active=new Map(),nativeLast=new Map(),modelLast=new Map(),modelByToken=new Map();let token=0,target=0,reuse=0,relative=0,frees=0,unmatched=0,nulls=0,firstNative=null,firstModel=null;
 for(const event of events){
  if(event.event==='crt-heap-allocation-return'||event.event==='zeroed-allocation-return'){
   assert(event.address&&event.requestedBytes>0&&!active.has(event.address));token++;const old=nativeLast.get(event.address)??null,addr=c.heap_model_alloc(event.requestedBytes)>>>0;assert(addr);const modelOld=modelLast.get(addr)??null;nativeLast.set(event.address,token);modelLast.set(addr,token);modelByToken.set(token,addr);active.set(event.address,token);
   if(event.event==='crt-heap-allocation-return'&&event.requestedBytes===0x530c){target++;if(old===modelOld)reuse++;if(firstNative===null){firstNative=event.address;firstModel=addr;}if(event.address-firstNative===addr-firstModel)relative++;}
  }else if(event.event==='crt-free-entry'||event.event==='crt-free-return'){
   if(event.event==='crt-free-entry'&&!event.address){nulls++;continue;}
   if((mode==='entry'&&event.event!=='crt-free-entry')||(mode==='successful-return'&&event.event!=='crt-free-return'))continue;
   if(event.event==='crt-free-return')assert(event.success);
   const id=active.get(event.address);if(id===undefined){unmatched++;continue;}assert.equal(c.heap_model_free(modelByToken.get(id)),1);active.delete(event.address);frees++;
  }else throw Error('unexpected heap event');
 }
 assert.equal(c.heap_model_ok(),1);assert.equal(token,proof.counts['crt-heap-allocation-return']+proof.counts['zeroed-allocation-return']);assert.equal(target,proof.counts.primaryAllocationsWithEnemyObjectSize);assert.equal(frees+unmatched,proof.counts.successfulFreeReturns);assert.equal(nulls,proof.counts.nullFreeEntries);results.push({mode,allocations:token,targetSizeAllocations:target,targetReuseIdentityMatches:reuse,targetRelativePositionMatches:relative,matchedFrees:frees,unmatchedFrees:unmatched,nullFreeEntries:nulls});
}
const result={verifiedFiniteObservedFreeReturnModelExperiment:true,callbacks:proof.callbacks,models:results,allNonNullFreeReturnsObservedSuccessful:true,debugDeliveryOrderAssumedMemoryOrder:true,actualCrossThreadMemoryOrderProved:false,earlierActivityAndOtherHeapPathsNotModeled:true,targetSizeIsNotProvenEnemy:true,actualOriginalAddressesProvidedToModel:false,originalHeapHistoryReconstructed:false,productionIntegrated:false,completeGame:false,nativeEquivalent:false,eventLogSha256:sha(raw),traceProofSha256:sha(proofRaw),largeWasmSha256:sha(wasm),toolSha256:sha(read(new URL(import.meta.url))),scope:'Both isolated models use the same finite original trace and synthetic heap; one applies the observed successful frees at entry, the other at their actual return. Cross-thread debugger delivery order is still an unproved approximation of actual heap-operation order, and earlier or other allocations remain omitted.'};
const out=resolve(R,'docs/porting/th14-heap-free-return-model-nov03.json'),encoded=JSON.stringify(result,null,2)+'\n';if(process.argv.includes('--check'))assert.equal(read(out,'utf8'),encoded);else{assert(!existsSync(out));write(out,encoded,{flag:'wx'});}console.log(JSON.stringify(result));
