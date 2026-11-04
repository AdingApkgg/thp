import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{WASI}from'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/camera-normalize-store-order-nov04'),sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const referencePath=resolve(root,'artifacts/th14/perspective-publication-native-cpu-nov04/verified.json'),referenceRaw=read(referencePath),reference=JSON.parse(referenceRaw);
assert(reference.actualWindowsX86D3dxServices&&reference.dllServicesDelegatedToActualReferenceCpu&&reference.unicornD3dxFloatingExecutionRejected);
assert.equal(reference.toolSha256,sha(read(resolve(root,'tools/th14-perspective-publication-native-cpu-nov04.py'))));
const nativeRaw=read(resolve(home,'native-stage4-source-read.json')),native=JSON.parse(nativeRaw);
assert(native.frozenReadOnlyRowsFromActiveCapture&&!native.captureAccepted);assert.equal(native.pendingYStoreRva,0x1bcaa4);assert.equal(native.pendingYAndZInstructionHex,'f30f116104f30f116908');
async function load(kind){
 const buildRaw=read(resolve(home,kind,'observer-build.json')),build=JSON.parse(buildRaw),wasm=read(resolve(home,kind,'observer.wasm'));
 assert.equal(sha(wasm),build.wasmSha256);for(const row of build.objectBindings)assert.equal(sha(read(row.path)),row.sha256);
 for(const[path,digest]of Object.entries(build.fixtureDependencyHashes))assert.equal(sha(read(path)),digest);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 return{c:instance.exports,wasmSha256:build.wasmSha256,buildSha256:sha(buildRaw)};
}
const old=await load('old-component'),candidate=await load('component');
const state=(c,point)=>{const bytes=Buffer.alloc(300);for(let word=0;word<75;word++)bytes.writeUInt32LE(c.normalize_phase_word(point,word)>>>0,word*4);return bytes;};
const input=(c,bytes)=>{assert.equal(bytes.length,300);for(let word=0;word<75;word++)assert.equal(c.normalize_input_word(word,bytes.readUInt32LE(word*4)),1);return c.normalize_run()>>>0;};
const differences=(a,b)=>Array.from({length:75},(_,word)=>word).filter(word=>a.readUInt32LE(word*4)!==b.readUInt32LE(word*4));
let comparedWords=0;const results=[];
for(let profile=0;profile<4;profile++){
 const rows=reference.rows.filter(row=>row.profile===profile),initial=Buffer.from(rows[0].nativeInputHex,'hex');
 assert.equal(input(old.c,initial),63);assert.equal(input(candidate.c,initial),255);
 assert.deepEqual(Array.from({length:8},(_,index)=>candidate.c.normalize_phase_order(index)>>>0),[0,1,2,3,4,6,7,5]);
 for(let point=0;point<6;point++){
  const expected=Buffer.from(rows.find(row=>row.point===point).nativeCopiedCameraHex,'hex');
  assert.deepEqual(differences(state(old.c,point),expected),[],`old profile${profile} point${point}`);
  assert.deepEqual(differences(state(candidate.c,point),expected),[],`candidate profile${profile} point${point}`);comparedWords+=150;
 }
 const raw=Buffer.from(rows.find(row=>row.point===4).nativeCopiedCameraHex,'hex'),normalized=Buffer.from(rows.find(row=>row.point===5).nativeCopiedCameraHex,'hex');
 for(const point of [6,7]){
  const expected=Buffer.from(raw);normalized.copy(expected,48,48,point===6?52:56);
  assert.deepEqual(differences(state(candidate.c,point),expected),[],`profile${profile} partial store point${point}`);comparedWords+=75;
 }
 results.push({profile,unchangedOldPoints:6,newPartialPoints:2});
}
const initial=Buffer.from(native.before.worldCameraHexAtWorkerEvent,'hex'),readExpected=Buffer.from(native.read.worldCameraHex,'hex'),copied=Buffer.from(native.after.copiedCameraHex,'hex');
assert.equal(input(old.c,initial),63);assert.equal(input(candidate.c,initial),255);
const actualRead=state(candidate.c,6),actualFinal=state(candidate.c,5),readDifferences=differences(actualRead,readExpected),copyDifferences=differences(actualFinal,copied);
const oldPointDifferences=Array.from({length:6},(_,point)=>({point,words:differences(state(old.c,point),readExpected)}));
write(resolve(home,'actual-read-point6.u32'),actualRead,{flag:'wx'});write(resolve(home,'actual-final-point5.u32'),actualFinal,{flag:'wx'});
const proof={verifiedNormalizeStoreBoundaries:readDifferences.length===0&&copyDifferences.length===0,actualReadDifferences:readDifferences,actualCopiedDifferences:copyDifferences,
 oldPointsCannotRepresentActualSourceRead:oldPointDifferences.every(row=>row.words.length>0),oldPointDifferences,syntheticProfiles:results,syntheticComparedWords:comparedWords,
 actualSourceReadWords:75,actualCopiedWords:75,candidateWasmSha256:candidate.wasmSha256,oldWasmSha256:old.wasmSha256,candidateBuildSha256:candidate.buildSha256,oldBuildSha256:old.buildSha256,
 nativeStage4FrozenRowsSha256:sha(nativeRaw),nativeCpuReferenceSha256:sha(referenceRaw),checkerSha256:sha(read(new URL(import.meta.url))),
 actualNativeReadPcMapsToNewPoint6:true,originalWholeCaptureAccepted:false,nativeGameStateValuesUsedOnlyAsIsolatedComponentInputs:true,nativeValuesProvidedToGameSession:false,
 rootProductionSourcesModified:false,completeGame:false,nativeEquivalent:false};
write(resolve(home,'component-verified.json'),JSON.stringify(proof,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(proof));
assert(proof.verifiedNormalizeStoreBoundaries);assert(proof.oldPointsCannotRepresentActualSourceRead);
