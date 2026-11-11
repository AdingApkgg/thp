import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=process.cwd();
const options=new Map(process.argv.slice(2).map(arg=>{const m=/^--(build|stock|native|output)=(.+)$/.exec(arg);assert.ok(m,'Use --build=, --stock=, --native= and optional --output=');return [m[1],m[2]];}));
for(const key of ['build','stock','native'])assert.ok(options.get(key),'Missing --'+key+'= path');
const buildDir=resolve(root,options.get('build')),stockDir=resolve(root,options.get('stock'));
const nativePath=resolve(root,options.get('native')),output=resolve(root,options.get('output')??buildDir);
mkdirSync(output,{recursive:true});
const load=p=>JSON.parse(readFileSync(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const build=load(resolve(buildDir,'build.json')),out={},sizes=[];
assert.equal(sha(readFileSync(resolve(stockDir,'th14.dat'))),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233','Original Japanese 1.00b DATA identity');
for(const [p,h]of Object.entries(build.sourceBindings??{}))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
assert.equal(sha(readFileSync(resolve(root,build.fixturePath))),build.fixtureSha256);
for(const row of build.currentProviders)assert.equal(sha(readFileSync(resolve(root,row.object))),row.objectSha256);
for(const mode of ['baseline','candidate']){
 const bytes=readFileSync(resolve(buildDir,mode+'.wasm'));assert.equal(sha(bytes),build.outputs[mode]);
 const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{'/stock':stockDir},returnOnExit:true});
 const env={memory};for(const i of WebAssembly.Module.imports(module))if(i.module==='env'&&i.kind==='function')env[i.name]=()=>{throw Error('Unexpected platform call '+i.name);};
 const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);sizes.push(instance.exports.session_bytes());assert.equal(instance.exports.run(),65);
 const words=Array.from(new Uint32Array(memory.buffer,instance.exports.data(),65));out[mode]=Array.from({length:5},(_,i)=>words.slice(i*13,i*13+13));
}
writeFileSync(resolve(output,'raw-results.json'),JSON.stringify(out,null,2)+'\n');
assert.equal(sizes[0],sizes[1],'Both real GameSession layouts agree');
const native=load(nativePath);
for(let i=0;i<5;i++){
 assert.deepEqual(out.candidate[i].slice(1,3),native.cases[i===4?1:i].controlCallbacksAfterEachPass);
 for(const mode of ['baseline','candidate']){
  assert.deepEqual(out[mode][i].slice(3,5),[1,2],'Exactly one actual overlay update per frame');
  assert.deepEqual(out[mode][i].slice(5,7),[1,2],'Exactly one actual normal update per frame');
  assert.equal(out[mode][i][11],i===4?0:1,'Worker return is independent of data adoption');
 }
}
assert.deepEqual(out.baseline[1].slice(1,3),[0,1],'Old Main-only read misses the live Overlay publication');
assert.deepEqual(out.candidate[1].slice(1,3),[1,2]);
assert.deepEqual(out.candidate.map(r=>r.slice(7,9)),[[1,1],[1,1],[1,2],[1,2],[1,1]],'Never run a second upload pump after Overlay');
assert.equal(out.candidate[4][12],0,'No successful worker join at post-overlay handoff');
assert.equal(out.baseline[4][12],1,'Existing Main resource-poll reaping remains verified');
const report={passed:true,runnerSha256:sha(readFileSync(import.meta.filename)),nativeProofSha256:sha(readFileSync(nativePath)),buildSha256:sha(readFileSync(resolve(buildDir,'build.json'))),controlledCases:5,gameSessionBytes:sizes[0],actualGameSessionAndAnm:true,nativeMainRegistry:true,baselineMissesOverlayEnable:true,candidateMatchesAllNativeCases:true,noDuplicateOverlay:true,noDuplicateNormal:true,noSecondResourcePump:true,workerStillRunningAtAdoption:true,successfulPostOverlayWorkerNotJoined:true,graphicsOrAudioDevicesOpened:0,priorArtifactObjectsUsed:build.priorArtifactObjectsUsed??true,fullApplicationSchedulingAccepted:false,completeGame:false};
writeFileSync(resolve(output,'component-results.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
