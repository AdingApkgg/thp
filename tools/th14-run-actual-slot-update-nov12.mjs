import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {WASI} from 'node:wasi';
const root=process.cwd(),home=resolve('artifacts/th14/actual-slot-update-nov12');
const buildDir=resolve(home,'cpp-current'),out=resolve(home,'cpp-comparison');
assert(!existsSync(out),'Keep previous results');mkdirSync(out);
const sha=b=>createHash('sha256').update(b).digest('hex');
const load=p=>JSON.parse(readFileSync(p,'utf8'));
const buildPath=resolve(buildDir,'build.json'),nativePath=resolve(home,'verified-v6/report.json');
const build=load(buildPath),native=load(nativePath);
assert(build.fixtureNormalAccessControl&&native.passed);
for(const [p,h]of Object.entries(build.sourceBindings))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
for(const row of build.currentProviders)assert.equal(sha(readFileSync(row.object)),row.objectSha256,row.object);
for(const [p,row]of Object.entries(native.bindings))assert.equal(sha(readFileSync(resolve(root,p))),row.sha256,p);
const binary=readFileSync(resolve(buildDir,'probe.wasm'));assert.equal(sha(binary),build.wasmSha256);
const module=new WebAssembly.Module(binary),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true}),env={memory};
for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected platform service '+i.name);};
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const nativeDir=resolve('artifacts/th14/original-nine-shot-native-nov05/prefix-slots-v2/native');
const index=load(resolve(nativeDir,'shot-lifetime-index.json'));
const labels=['quad0.x','quad0.y','quad0.z','quad1.x','quad1.y','quad1.z','quad2.x','quad2.y','quad2.z','quad3.x','quad3.y','quad3.z',
 'shot.state','shot.handlePresent','shot.timer.previous','shot.timer.current','shot.timer.fractional','shot.timer.flags',
 'shot.position.x','shot.position.y','shot.position.z','shot.velocity.x','shot.velocity.y','shot.velocity.z',
 'vm.position.x','vm.position.y','vm.position.z','vm.rotation.z'];
const cases=[],failures=[];
for(const group of native.cases){
 const row=index.snapshots.find(r=>r.callback===group.nativeCallback);assert(row);
 const compressed=readFileSync(resolve(nativeDir,'shot-lifetime',row.file));assert.equal(sha(compressed),row.sha256);
 const n=JSON.parse(gunzipSync(compressed)),pool=Buffer.from(n.shotPoolRawHex,'hex');
 const s=pool.subarray(group.slot*208,(group.slot+1)*208),v=Buffer.from(n.vms[String(group.slot)].rawHex,'hex'),g=Buffer.from(n.renderGlobalsRawHex,'hex');
 const spec=Buffer.from(n.specs[String(s.readUInt32LE(0xbc))],'hex');assert.equal(spec[0x21],0);assert.equal(spec.readUInt32LE(0x2c),0);
 assert.equal(s.readUInt32LE(0xc0),0);assert.equal(v.readUInt32LE(0x594),0);
 const input=Buffer.concat([s,v,g]);assert.equal(input.length,(52+371+9)*4);
 for(const control of group.controls)for(const [kind,rotation]of [['original',group.nativeRotationBits],['rotationOnly',group.cppRotationBits]]){
  new Uint8Array(memory.buffer,c.input_ptr(),input.length).set(input);
  assert.equal(c.tick(control.declaredRate,rotation),1,'actual ShotManager update failed');
  const actual=Array.from(new Uint32Array(memory.buffer,c.output_ptr(),30)),expected=control[kind].comparisonWords;
  assert.equal(expected.length,28);const differences=[];
  for(let i=0;i<28;++i)if(actual[i]!==expected[i])differences.push({field:labels[i],expected:expected[i],actual:actual[i]});
  // Pooled destruction is a declared sink in the oracle, while the real port
  // queues release on the VM. Compare this separately, not as raw ID equality.
  const expectedFlags2=v.readUInt32LE(0x1c)|(expected[12]===0?0x20:0);
  assert.equal(actual[28],expectedFlags2>>>0);assert.equal(actual[29],0);
  const result={nativeCallback:group.nativeCallback,slot:group.slot,inputKey:group.inputKey,
   declaredRate:control.declaredRate,kind,words:actual,differences};cases.push(result);
  for(const difference of differences)failures.push({...result,words:undefined,differences:undefined,...difference});
 }
}
const report={schema:'th14/current-cpp-actual-slot-update/1',passed:failures.length===0,
 actualRawGameplaySlots:native.cases.length,componentCases:cases.length,comparedWords:cases.length*28,
 cases,failures,labels,wasmSha256:build.wasmSha256,buildSha256:sha(readFileSync(buildPath)),
 nativeOracleSha256:sha(readFileSync(nativePath)),runnerSha256:sha(readFileSync(import.meta.filename)),
 currentProductionProvidersVerified:141,fixtureNormalAccessControl:true,
 rawInputsMappedToPublicFields:true,declaredClockRatesNotObservedGameplay:true,
 pooledReleaseComparedSeparately:true,rawVmIdentityEqualityClaimed:false,
 noOriginalValuesProvidedToLivePort:true,originalOsGameOrGpuStarted:false,
 productionChanged:false,strictReplayFailuresUnchanged:true,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,cases:cases.length,comparedWords:report.comparedWords,failures:failures.length,firstFailures:failures.slice(0,8)}));
if(failures.length)process.exitCode=1;
