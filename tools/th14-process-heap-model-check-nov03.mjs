// Compare a finite WASI model against 15 standalone x86 Windows heap runs.
import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/replay-candidates-second-nov03/process-heap-model-v3'),native=resolve(root,'artifacts/th14/replay-candidates-second-nov03/process-heap-scenarios-msvc'),sha=x=>createHash('sha256').update(x).digest('hex');
assert(process.argv.slice(2).every(x=>x==='--check')&&process.argv.slice(2).length<=1);
const build=JSON.parse(read(resolve(home,'build.json'))),plan=JSON.parse(read(resolve(native,'process-end.json')));assert.equal(build.sourceSha256,sha(read(resolve(root,'tools/th14-process-heap-model-nov03.cpp'))));assert.equal(plan.sourceSha256,sha(read(resolve(root,'tools/th14-process-heap-scenarios-nov03.c'))));assert.equal(plan.scenarios,5);assert.equal(plan.runsPerScenario,3);assert(!plan.originalGameLaunched&&!build.productionIntegrated);
const freeOrders=[[1,3,5,7],[0,2,4,6],[7,5,3,1],[2,3,4,5],[0,1,2,3,4,5,6,7]],observed=[];
for(const record of plan.cases){
 const b=read(resolve(native,`case-${record.case}-run-${record.run}.bin`));assert.equal(sha(b),record.sha256);assert.equal(b.length,208);assert.equal(b.readUInt32LE(0),0x53485054);assert.equal(b.readUInt32LE(4),record.case);const count=b.readUInt32LE(12);assert.equal(count,freeOrders[record.case].length);
 const initial=Array.from({length:8},(_,i)=>b.readUInt32LE(16+4*i)),replacement=Array.from({length:count},(_,i)=>b.readUInt32LE(48+4*i)),declared=Array.from({length:count},(_,i)=>b.readUInt32LE(80+4*i));assert.deepEqual(declared,freeOrders[record.case]);assert.equal(new Set(initial).size,8);assert.equal(new Set(replacement).size,count);assert(Array.from({length:8+count},(_,i)=>b.readUInt32LE(112+4*i)).every(x=>x===0x530c));assert(Array.from({length:count},(_,i)=>b.readUInt32LE(176+4*i)).every(x=>x===1));
 const order=replacement.map(address=>{const index=initial.indexOf(address);return index<0?null:index;});observed.push({case:record.case,run:record.run,freeSlots:declared,reusedInitialSlots:order,initialRelativeDeltas:initial.slice(1).map((x,i)=>x-initial[i])});
}
assert.equal(observed.length,15);
const outputs=[];
for(const variant of build.variants){
 const bytes=read(resolve(home,variant.name+'.wasm'));assert.equal(sha(bytes),variant.wasmSha256);const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;let matches=0;const mismatches=[];
 for(const row of observed){
  c.heap_model_reset(0x20000000,0x100000);assert.equal(c.heap_model_ok(),1);const initial=Array.from({length:8},()=>c.heap_model_alloc(0x530c)>>>0);assert(initial.every(Boolean));assert.equal(new Set(initial).size,8);assert.deepEqual(initial.slice(1).map((x,i)=>x-initial[i]),row.initialRelativeDeltas);
  for(const slot of freeOrders[row.case])assert.equal(c.heap_model_free(initial[slot]),1);const result=freeOrders[row.case].map(()=>{const value=c.heap_model_alloc(0x530c)>>>0;const index=initial.indexOf(value);return index<0?null:index;});if(JSON.stringify(result)===JSON.stringify(row.reusedInitialSlots))matches++;else mismatches.push({case:row.case,run:row.run});assert.equal(c.heap_model_ok(),1);
 }
 c.heap_model_reset(0x20000000,0x100000);const a=c.heap_model_alloc(0x530c)>>>0;assert(a);assert.equal(c.heap_model_free(a),1);assert.equal(c.heap_model_free(a),0);c.heap_model_reset(0xfffffff8,16);assert.equal(c.heap_model_ok(),0);assert.equal(c.heap_model_alloc(0x530c),0);
 outputs.push({name:variant.name,matchedRuns:matches,mismatchedRuns:mismatches,wasmSha256:variant.wasmSha256});
}
assert.equal(outputs.find(x=>x.name==='candidate').matchedRuns,15);assert(outputs.find(x=>x.name==='no-merge').matchedRuns<15);assert(outputs.find(x=>x.name==='fifo').matchedRuns<15);
const result={verifiedFiniteHelperHeapModel:true,scenarioCount:5,runs:15,observed,models:outputs,doubleFreeRejected:true,virtualRangeOverflowRejected:true,modelReceivesOnlyDeclaredFreeSlotOrder:true,hostNativePointerValuesProvidedToModel:false,originalGameLaunched:false,originalGameHeapHistoryReproduced:false,actualWindowsAllocatorAlgorithmProved:false,productionIntegrated:false,completeGame:false,nativeEquivalent:false,modelSourceSha256:build.sourceSha256,helperSourceSha256:plan.sourceSha256,verifierSha256:sha(read(new URL(import.meta.url))),scope:'One candidate with contiguous coalescing, best fit and recency tie-break matches only these fifteen standalone x86 helper runs. Inputs to the model are synthetic addresses and declared free-slot orders; actual helper addresses are used solely to classify observations. No claim about TH14 heap history, general Windows allocation or full-game equivalence.'};
const out=resolve(root,'docs/porting/th14-process-heap-model-nov03.json'),encoded=JSON.stringify(result,null,2)+'\n';if(process.argv.includes('--check'))assert.equal(read(out,'utf8'),encoded);else{assert(!existsSync(out));write(out,encoded,{flag:'wx'});}console.log(JSON.stringify({verifiedFiniteHelperHeapModel:true,runs:15,models:outputs.map(({name,matchedRuns})=>({name,matchedRuns})),productionIntegrated:false,completeGame:false}));
