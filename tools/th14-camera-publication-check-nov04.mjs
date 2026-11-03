import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';

assert.equal(process.argv.length,4);assert.equal(process.argv[2],'--candidate');
const root=resolve(import.meta.dirname,'..'),home=resolve(root,process.argv[3]);
const scope=relative(resolve(root,'artifacts/th14'),home);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const nativeBytes=read(resolve(home,'native-component.json')),native=JSON.parse(nativeBytes);
const buildBytes=read(resolve(home,'core/component-build.json')),build=JSON.parse(buildBytes);
assert(native.executedOriginalDrawBranchesAndWorkerCopy&&native.syntheticCamerasAndCpuSchedule&&!native.liveOriginalProcess);
assert(!native.originalInstructionsModified&&native.controlledCases===50&&native.publicationCases===36);
const instantiate=async(name,digest)=>{
 const bytes=read(resolve(home,'core',name));assert.equal(sha(bytes),digest);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 return instance.exports;
};
const candidate=await instantiate('component.wasm',build.candidateSha256),prior=await instantiate('prior-component.wasm',build.priorSha256);
let cases=0,publicationCalls=0,copiedScenes=0,priorCopiedRightDifferences=0,propagatedFailures=0;
for(const row of native.rows)for(const fail of [0,1])for(const pending of [0,1]){
 assert.equal(candidate.camera_publication_case(row.foreground,row.flags,row.fade,fail,pending),1);
 assert.equal(prior.camera_publication_case(row.foreground,row.flags,row.fade,fail,pending),1);
 const actual=Array.from({length:14},(_,i)=>candidate.camera_publication_value(i)>>>0);
 const old=Array.from({length:14},(_,i)=>prior.camera_publication_value(i)>>>0);
 assert.equal(actual[0],Number(!(row.publishedBeforePerspective&&fail)));
 assert.equal(actual[1],Number(row.publishedBeforePerspective));
 assert.equal(actual[5],Number(row.publishedBeforePerspective&&pending));
 if(row.publishedBeforePerspective){
  assert.deepEqual(actual.slice(2,5),row.workerCopiedRight);
  assert.deepEqual(actual.slice(12,14),[0x41500000,0xc0e00000]);
  if(pending){
   assert.deepEqual(actual.slice(6,9),row.workerCopiedRight);
   assert.notDeepEqual(old.slice(6,9),row.workerCopiedRight);
   ++priorCopiedRightDifferences;++copiedScenes;
  }
  if(fail)++propagatedFailures;
 }
 assert.equal(old[1],0);
 ++cases;publicationCalls+=actual[1];
}
assert.equal(cases,200);assert.equal(publicationCalls,144);assert.equal(copiedScenes,72);
assert.equal(priorCopiedRightDifferences,72);assert.equal(propagatedFailures,72);
const result={verifiedControlledCameraPublicationComponent:true,cases,publicationCalls,copiedScenes,
 priorCopiedRightDifferences,propagatedFailures,originalDrawBranchesAndWorkerCopyExecuted:true,
 projectionBoundaryIsOriginalPublicationInstruction:true,syntheticCpuScheduleAndCameras:true,
 oldRecordingOrderRecovered:false,copyWordInterleavingsImplemented:false,oldCameraOrRngFailuresClosed:false,
 rootGameplaySourcesModified:false,productionIntegrated:false,completeGame:false,nativeEquivalent:false,
 nativeProofSha256:sha(nativeBytes),componentBuildSha256:sha(buildBytes),
 candidateWasmSha256:build.candidateSha256,priorWasmSha256:build.priorSha256,
 fixtureSha256:build.fixtureSha256,toolSha256:sha(read(import.meta.filename))};
write(resolve(home,'component-verified.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
