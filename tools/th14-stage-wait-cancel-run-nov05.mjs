// Semantic lifetime controls for the exact cancellation component; no assets.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]);
assert(home.startsWith(resolve(root,'artifacts/th14')+'\\')||home.startsWith(resolve(root,'artifacts/th14')+'/'));
const buildBytes=readFileSync(resolve(home,'build.json')),build=JSON.parse(buildBytes);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex'),results={};
for(const name of ['before','after']){
 const bytes=readFileSync(resolve(home,name,'component.wasm'));
 assert.equal(sha(bytes),build.builds[name].wasmSha256);
 assert.equal(sha(readFileSync(resolve(home,name,'fixture.cpp'))),build.builds[name].fixtureSha256);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});
 wasi.initialize(instance);const returned=instance.exports.run();
 const words=Array.from({length:9},(_,i)=>instance.exports.value(i)>>>0);
 assert.equal(returned,words[0]);
 results[name]={failures:words[0],checks:words[1],firstFailure:words[2],
  hostCancellations:words[3],decodeCancellations:words[4],releases:words[5],mask:words[6],
  waitStillActive:words[7]===1,pendingUploadReferences:words[8]};
}
assert.equal(results.before.firstFailure,2);
assert(results.before.failures>=5);
assert.equal(results.before.hostCancellations,0);
assert.equal(results.before.waitStillActive,true);
assert.equal(results.before.pendingUploadReferences,1);
assert.equal(results.after.failures,0);
assert.equal(results.after.firstFailure,0);
// Three recording release checks per cancellation; decode is checked in both.
assert.equal(results.after.checks,results.before.checks+9);
assert.equal(results.after.hostCancellations,3);
assert.equal(results.after.decodeCancellations,3);
assert.equal(results.after.releases,3);
assert.equal(results.after.mask,0);
assert.equal(results.after.waitStillActive,false);
assert.equal(results.after.pendingUploadReferences,0);
const report={schema:'th14/stage-wait-cancel-component/1',passed:true,results,
 buildSha256:sha(buildBytes),toolSha256:sha(readFileSync(import.meta.filename)),
 noRequestedResourcePhaseControl:true,repeatedCancelControl:true,
 staleBeforeDispatchControl:true,staleAfterDispatchControl:true,newGenerationControl:true,
 directQueuedUploadHelperControl:true,
 ordinaryApplicationExecuted:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(home,'verified.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,before:results.before,after:results.after,ordinaryApplicationExecuted:false}));
