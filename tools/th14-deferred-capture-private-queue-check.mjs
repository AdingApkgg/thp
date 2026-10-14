// Compile a private queue implementation against immutable original enqueue/
// empty-target retirement receipts. No production edit, GPU shim or game child.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/deferred-capture-prototype-oct14');
const sha=b=>createHash('sha256').update(b).digest('hex'),bindings={};
const read=name=>{const b=readFileSync(resolve(root,name));bindings[name]={bytes:b.length,sha256:sha(b)};return b;};
const nativePath='docs/porting/th14-staged-loader-capture-queue-verified-oct14.json';
const native=JSON.parse(read(nativePath));
assert.equal(sha(read('tools/th14-staged-loader-capture-queue-evidence-check.py')),native.verifierSha256);
assert(native.captureQueueEvidencePassed&&!native.nativeEquivalent&&!native.productionChanged);
const boundary=JSON.parse(read('docs/porting/th14-staged-loader-host-boundary-verified-oct14.json'));
assert(boundary.priorReportFieldLabelCorrection.includes('words2..5 are SOURCE'));
mkdirSync(out,{recursive:true});
const header=`#pragma once
#include <array>
#include <cstdint>
namespace th11 {
struct DeferredCaptureRequestTh14 {
 std::int32_t file_index=-1,texture_index=0;
 // Both rectangles retain the original x/y/width/height record words.
 std::array<std::int32_t,4> source{},destination{};
};
static_assert(sizeof(DeferredCaptureRequestTh14)==40);
struct DeferredCaptureQueueTh14 {
 std::array<DeferredCaptureRequestTh14,4> slots{};
 std::int32_t first_file_index()const noexcept{return slots[0].file_index;}
 std::int32_t enqueue(const DeferredCaptureRequestTh14& request) noexcept {
  for(auto& slot:slots)if(slot.file_index<0){slot=request;break;}
  return 0; // Original44bdd0 also returns0 when all slots are occupied.
 }
 template<class Copy> void consume(Copy&& copy){
  for(auto& slot:slots)if(slot.file_index>=0){
   copy(slot); // Null target and GetSurfaceLevel error still retire the record.
   slot.file_index=-1;
  }
 }
};
}
`;
const fixture=`#include "DeferredCaptureQueueTh14.hpp"
#include <cstring>
using namespace th11;
static std::int32_t input_words[64],output_words[64];
extern "C" unsigned capture_input(){return unsigned(input_words);}
extern "C" unsigned capture_output(){return unsigned(output_words);}
extern "C" int capture_run(int operation){
 DeferredCaptureQueueTh14 queue;
 if(operation)std::memcpy(queue.slots.data(),input_words,160);
 output_words[40]=queue.first_file_index();output_words[41]=0;output_words[42]=0;
 if(operation==1){DeferredCaptureRequestTh14 request;std::memcpy(&request,input_words+40,40);output_words[43]=queue.enqueue(request);}
 if(operation==2)queue.consume([&](const auto& record){
  output_words[44+output_words[41]]=record.file_index;
  output_words[48+output_words[41]]=queue.first_file_index();
  ++output_words[41];return input_words[60]; // Explicit controlled result; no GPU.
 });
 std::memcpy(output_words,queue.slots.data(),160);output_words[42]=queue.first_file_index();return 0;
}
`;
for(const [name,source] of [['DeferredCaptureQueueTh14.hpp',header],['fixture.cpp',fixture]]){
 const p=resolve(out,name);if(existsSync(p))assert.equal(readFileSync(p,'utf8'),source,'immutable prototype source');else writeFileSync(p,source);
}
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const flags=['-O2','-std=c++17','-fno-exceptions','-fno-rtti','-nostartfiles','-Wl,--no-entry',...['capture_input','capture_output','capture_run'].map(n=>'-Wl,--export='+n)];
execFileSync(compiler,[...flags,resolve(out,'fixture.cpp'),'-o',resolve(out,'queue.wasm')],{cwd:root,stdio:'inherit',windowsHide:true});
const module=new WebAssembly.Module(readFileSync(resolve(out,'queue.wasm')));assert.deepEqual(WebAssembly.Module.imports(module),[]);
const {exports:e}=new WebAssembly.Instance(module,{}),input=e.capture_input(),output=e.capture_output();
const run=(op,slots,args=[],result=0)=>{
 const data=new Int32Array(e.memory.buffer);data.fill(0,input/4,input/4+64);
 if(slots)for(let index=0;index<4;index++)data.set([slots[index],...Array.from({length:9},(_,j)=>101+j)],input/4+index*10);
 if(args.length)data.set(args,input/4+40);data[input/4+60]=result;
 assert.equal(e.capture_run(op),0);return [...new Int32Array(e.memory.buffer,output,64)];
};
const constructor=run(0);assert.deepEqual([0,10,20,30].map(n=>constructor[n]),[-1,-1,-1,-1]);
const enqueueCases=native.enqueues.map(row=>{
 const words=run(1,row.before,row.arguments);
 const expected=row.before.flatMap(n=>[n,...Array.from({length:9},(_,j)=>101+j)]);
 if(row.firstFreeSlot!==null)expected.splice(row.firstFreeSlot*10,10,...row.arguments);
 assert.deepEqual(words.slice(0,40),expected);
 assert.deepEqual([0,10,20,30].map(n=>words[n]),row.after);
 assert.equal(words[43],0);
 if(row.firstFreeSlot!==null)assert.deepEqual(words.slice(row.firstFreeSlot*10,row.firstFreeSlot*10+10),row.arguments);
 return {before:row.before,arguments:row.arguments,firstFreeSlot:row.firstFreeSlot,after:row.after,matchedOriginalRecordWords:true};
});
const retirementCases=[];
for(const row of native.nullTargetRetirements){
 for(const result of [0,1,-2147467259]){
  const words=run(2,row.before,[],result);
  assert.deepEqual([0,10,20,30].map(n=>words[n]),row.after);
  const expected=row.before.filter(n=>n>=0);assert.equal(words[41],expected.length);
  assert.deepEqual(words.slice(44,44+expected.length),expected);
  assert.equal(words[40],row.before[0]);assert.equal(words[42],row.after[0]);
  retirementCases.push({before:row.before,after:row.after,controlledCopyResult:result,consumedFileOrder:expected,matchedOriginalEmptyTargetRetirement:true});
 }
}
const pending=run(1,[-1,0,1,25],[3,2,32,16,384,448,3,5,128,128]);assert.equal(pending[42],3);
const otherPending=run(3,native.firstSlotOnlyWait.declaredSlots);assert.equal(otherPending[42],-1);
const report={privateQueueEvidenceVerified:true,productionChanged:false,completeGame:false,nativeEquivalent:false,
 constructorIndices:[-1,-1,-1,-1],enqueueCases,retirementCases,
 enqueueCasesMatched:enqueueCases.length,retirementCasesMatched:retirementCases.length,
 firstSlotPredicateIsSignedFileIndex:true,allSlotsEmptyPredicateNotUsed:true,
 sourceSha256:sha(Buffer.from(header)),fixtureSha256:sha(Buffer.from(fixture)),wasmSha256:sha(readFileSync(resolve(out,'queue.wasm'))),
 flags,bindings,toolSha256:sha(readFileSync(import.meta.filename)),
 retainedFixtureSetupFailure:{path:'artifacts/th14/deferred-capture-prototype-oct14/queue-initial-crt-imports-failed.wasm',sha256:sha(readFileSync(resolve(out,'queue-initial-crt-imports-failed.wasm'))),reason:'Initial command CRT link unexpectedly imported args_get/args_sizes_get/proc_exit. It stopped at the import assertion before any queue case. Current no-entry fixture links without startup files and has no imports.'},
 scope:'Private four40-byte-record queue compared with immutable18 original44bdd0 enqueues and5 actual null-target4690d0 retirements, with explicit controlled callback return variants. Source/destination labels follow later corrected Native x/y/width/height meaning. No copy target or GPU service is simulated; callback return controls test retirement mechanics only. OrdinaryPause is not enqueued. Application/End-menu integration, successful or failed real backend copies,80-frame second capture, Native pixels, resource lookup lifetime and whole-game1:1 remain unverified.'};
const outputPath=resolve(root,'docs/porting/th14-deferred-capture-private-queue-verified-oct14.json');
writeFileSync(outputPath,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({privateQueueEvidenceVerified:true,enqueueCases:enqueueCases.length,retirementCases:retirementCases.length,productionChanged:false}));
