// Compare two synthetic model inputs using the same recorded debug delivery order.
import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/replay-candidates-second-nov03/combined-heap-original/main'),M=resolve(R,'artifacts/th14/replay-candidates-second-nov03/process-heap-model-large'),sha=x=>createHash('sha256').update(x).digest('hex');
assert(process.argv.slice(2).every(x=>x==='--check')&&process.argv.slice(2).length<=1);
const proofRaw=read(resolve(R,'docs/porting/th14-combined-heap-trace-nov03.json')),proof=JSON.parse(proofRaw),eventRaw=read(resolve(H,'native/crt-heap-events.jsonl')),events=eventRaw.toString().trim().split('\n').map(JSON.parse),build=JSON.parse(read(resolve(M,'build.json'))),wasm=read(resolve(M,'large.wasm')),control=JSON.parse(read(resolve(R,'docs/porting/th14-crt-boot-model-trace-nov03.json')));
assert(proof.verifiedFiniteOriginalCombinedHeapTrace&&proof.debugExceptions===0&&control.capacityExtensionControlMatched);assert.equal(sha(eventRaw),proof.eventLogSha256);assert.equal(sha(wasm),build.wasmSha256);assert.equal(sha(wasm),control.largeWasmSha256);assert.equal(sha(read(resolve(R,'tools/th14-process-heap-model-nov03.cpp'))),build.baseSourceSha256);
async function model(){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);instance.exports.heap_model_reset(0x20000000,0x10000000);return instance.exports;}
const specs=[{name:'primaryOnly',c:await model(),includeZeroed:false},{name:'primaryAndZeroed',c:await model(),includeZeroed:true}];
for(const state of specs){
 const active=new Map(),nativeLast=new Map(),modelLast=new Map(),modelByToken=new Map();let token=0,matchedFrees=0,unknownFrees=0,nullFrees=0,primary=0,zeroed=0,target=0,targetReuse=0,targetRelative=0,firstNative=null,firstModel=null;
 for(const event of events){
  if(event.event==='crt-heap-allocation-return'||event.event==='zeroed-allocation-return'){
   assert(event.address&&event.requestedBytes>0);token++;const old=nativeLast.get(event.address)??null;nativeLast.set(event.address,token);
   if(event.event==='zeroed-allocation-return'){zeroed++;if(!state.includeZeroed)continue;}else primary++;
   assert(!active.has(event.address));const addr=state.c.heap_model_alloc(event.requestedBytes)>>>0;assert(addr);const modelOld=modelLast.get(addr)??null;modelLast.set(addr,token);modelByToken.set(token,addr);active.set(event.address,token);
   if(event.event==='crt-heap-allocation-return'&&event.requestedBytes===0x530c){target++;if(old===modelOld)targetReuse++;if(firstNative===null){firstNative=event.address;firstModel=addr;}if(event.address-firstNative===addr-firstModel)targetRelative++;}
  }else{
   assert.equal(event.event,'crt-free-entry');if(!event.address){nullFrees++;continue;}const old=active.get(event.address);if(old===undefined){unknownFrees++;continue;}assert.equal(state.c.heap_model_free(modelByToken.get(old)),1);active.delete(event.address);matchedFrees++;
  }
 }
 assert.equal(state.c.heap_model_ok(),1);assert.equal(primary,proof.counts['crt-heap-allocation-return']);assert.equal(zeroed,proof.counts['zeroed-allocation-return']);assert.equal(target,proof.counts.primaryAllocationsWithEnemyObjectSize);Object.assign(state,{primary,zeroed,target,targetReuse,targetRelative,matchedFrees,unknownFrees,nullFrees});delete state.c;delete state.includeZeroed;
}
const result={verifiedFiniteSameTraceHeapScopeExperiment:true,callbacks:proof.callbacks,events:events.length,models:specs,primarySize530cIsNotProvenEnemy:true,modelReceivesOnlySizesAndObservedLifetimeOrder:true,actualOriginalAddressesProvidedToModel:false,debugDeliveryOrderAssumedMemoryOrderForExperiment:true,freeSuccessAssumedForExperiment:true,earlierActivityAndOtherHeapPathsNotModeled:true,originalHeapHistoryReconstructed:false,productionIntegrated:false,completeGame:false,nativeEquivalent:false,eventLogSha256:sha(eventRaw),traceProofSha256:sha(proofRaw),largeWasmSha256:sha(wasm),toolSha256:sha(read(new URL(import.meta.url))),scope:'Both isolated models process the same debugger event delivery order; the first omits zeroed allocations and the second includes them. Debug delivery order and free success are assumptions; loader before attach and other paths are omitted. The 0x530c primary allocation size is only a size filter, not proof of enemy identity.'};
const out=resolve(R,'docs/porting/th14-combined-heap-model-trace-nov03.json'),encoded=JSON.stringify(result,null,2)+'\n';if(process.argv.includes('--check'))assert.equal(read(out,'utf8'),encoded);else{assert(!existsSync(out));write(out,encoded,{flag:'wx'});}console.log(JSON.stringify(result));
