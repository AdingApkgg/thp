import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,existsSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=process.cwd(),options=new Map(process.argv.slice(2).map(arg=>{
 const m=/^--(build|native|ascii|output|negative)=(.+)$/.exec(arg);assert(m,'Use --build=, --native=, --ascii= and optional --output=');return[m[1],m[1]==="negative"?m[2]:resolve(root,m[2])];
}));
if(options.has('negative'))assert.equal(options.get('negative'),'ignore-control');
for(const name of ['build','native','ascii'])assert(options.has(name),'Missing --'+name);
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(p),load=p=>JSON.parse(read(p));
const buildDir=options.get('build'),nativeDir=options.get('native'),buildPath=resolve(buildDir,'build.json');
const output=options.get('output')??buildDir;mkdirSync(output,{recursive:true});
assert(!existsSync(resolve(output,'result.json')),'Choose a new output directory to preserve earlier results');
const build=load(buildPath),nativePath=resolve(nativeDir,'native.json'),native=load(nativePath);
for(const [p,h]of Object.entries({...build.sourceBindings,...build.observerBindings}))assert.equal(sha(read(resolve(root,p))),h,p);
const provider=load(build.providerBuild);assert.equal(sha(read(build.providerBuild)),build.providerBuildSha256);
for(const row of provider.currentProviders)assert.equal(sha(read(row.object)),row.objectSha256);
const bytes=read(resolve(buildDir,'probe.wasm'));assert.equal(sha(bytes),build.wasmSha256);
const ascii=read(options.get('ascii'));assert.equal(sha(ascii),native.asciiSha256);
const expectedRaw=read(resolve(nativeDir,'snapshots.u32'));assert.equal(sha(expectedRaw),native.snapshotsSha256);
const expected=new Uint32Array(expectedRaw.buffer,expectedRaw.byteOffset,expectedRaw.length/4);
const module=new WebAssembly.Module(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
let forbidden=0;const env={memory};
for(const item of WebAssembly.Module.imports(module))if(item.module==='env'&&item.kind==='function')env[item.name]=()=>{++forbidden;throw Error('Unexpected platform call '+item.name);};
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
const instance=new WebAssembly.Instance(module,{env,wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,p=c.allocate(ascii.length);new Uint8Array(memory.buffer,p,ascii.length).set(ascii);assert.equal(c.setup(p,ascii.length),1);c.release(p);
const cases=[];let totalWords=0,totalFrames=0;
for(const record of native.cases){
 assert.equal(c.begin(record.rate),1);let at=record.byteOffset/4;const differences=[];let mismatchedWords=0,mismatchedFrames=0,comparedWords=0;
 for(let frame=0;frame<=record.frames;frame++){
  assert.equal(expected[at],frame);const count=6+expected[at+1]*303,e=Array.from(expected.slice(at,at+count));at+=count;
  const length=c.step(frame,record.finishBeforeUpdate,options.has("negative")?0:frame>=record.freezeBegin&&frame<record.freezeEnd?record.frozenFlags:0);assert(length,'Actual manager update succeeded at '+frame+' '+Array.from(new Uint32Array(memory.buffer,c.failure_data(),8)));
  const a=Array.from(new Uint32Array(memory.buffer,c.data(),length));let different=false;comparedWords+=count;
  if(length!==count){different=true;++mismatchedWords;if(differences.length<80)differences.push({frame,field:'snapshotLength',native:count,cpp:length});}
  for(let i=0;i<Math.min(length,count);i++)if(e[i]!==a[i]){
   different=true;++mismatchedWords;
   if(differences.length<80)differences.push({frame,vm:i<6?null:Math.floor((i-6)/303),field:i<6?['frame','vmCount','scriptSeed','scriptCalls','gameplaySeed','gameplayCalls'][i]:(i-6)%303,native:e[i],cpp:a[i]});
  }
  if(different)++mismatchedFrames;
  if(different&&mismatchedFrames===1){writeFileSync(resolve(output,`first-mismatch-${record.name}.json`),JSON.stringify({frame,expected:e,actual:a},null,2)+'\n',{flag:'wx'});}
  ++totalFrames;
 }
 assert.equal(at*4,record.byteOffset+record.byteLength);c.close();totalWords+=comparedWords;
 cases.push({name:record.name,rate:record.rate,frozenFlags:record.frozenFlags,finishBeforeUpdate:record.finishBeforeUpdate,frames:record.frames+1,comparedWords,mismatchedFrames,mismatchedWords,differences});
}
assert.equal(forbidden,0);
const report={passed:cases.every(c=>c.mismatchedFrames===0),cases,totalFrames,totalWords,wordsPerVm:303,
 negativeControl:options.get("negative")??null,actualOriginalFactoryAndUpdates:true,actualCurrentLoadingOwnerAndManager:true,normalAccessControl:true,
 originalControlConsumers:true,controlFlagProducerDeclared:true,finishWhileFrozen:true,
 handlesAndRegistryLinksComparedWithoutNormalization:true,graphicsOrAudioDevicesOpened:0,
 physicalSchedulingAccepted:false,wholeGameAccepted:false,completeGame:false,
 bindings:{runner:sha(read(import.meta.filename)),native:sha(read(nativePath)),build:sha(read(buildPath))}};
writeFileSync(resolve(output,'result.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({...report,cases:cases.map(c=>({...c,differences:c.differences.slice(0,8)}))}));
if(!report.passed)process.exitCode=1;
