import assert from'node:assert/strict';import{readFileSync,writeFileSync}from'node:fs';import{WASI}from'node:wasi';import{createHash}from'node:crypto';
import{parseArgs}from'node:util';import{resolve,join}from'node:path';
const{values}=parseArgs({options:{native:{type:'string'},build:{type:'string'},output:{type:'string'}}});assert(values.native&&values.build&&values.output);
const native=JSON.parse(readFileSync(resolve(values.native,'report.json'))),build=JSON.parse(readFileSync(resolve(values.build,'build.json'))),bytes=readFileSync(resolve(values.build,'stack.wasm'));
assert.equal(createHash('sha256').update(bytes).digest('hex'),build.wasmSha256);
const w=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:w.wasiImport});w.initialize(instance);const c=instance.exports;
let compared=0,oldZeroFailures=0;
for(const row of native.cases.filter(x=>x.alignment===4)){
 assert.equal(c.run(+row.areaCircle,+row.targetRectangle,row.targetDelta,row.seed,row.priorScratch,1),1);
 const actual=Array.from({length:9},(_,i)=>c.value(i)>>>0);
 assert.equal(actual[0],row.damage);assert.equal(actual[1],1);assert.deepEqual(actual.slice(2,5),row.factory.position);assert.equal(actual[5],row.factory.rotation);assert.deepEqual(actual.slice(6,8),row.scriptRng);assert.equal(actual[8],row.factory.position[2]);
 assert.equal(c.run(+row.areaCircle,+row.targetRectangle,row.targetDelta,row.seed,row.priorScratch,0),1);
 if(c.value(4)!==row.factory.position[2])++oldZeroFailures;++compared;
}
assert.equal(compared,32);assert.equal(oldZeroFailures,20);
const report={referenceCollectorEntryAlignment:4,nativeCasesCompared:compared,allPositionWordsRotationDamageAndScriptRngEqual:true,oldZeroZControlsFailed:oldZeroFailures,otherAlignmentNotAccepted:true,wasmSha256:createHash('sha256').update(bytes).digest('hex'),originalLiveZProvidedToGameEngine:false,productionFixtureExecuted:true,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(values.output),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
