import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync,existsSync,statfsSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),options=new Map();
for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i]?.replace(/^--/,'');assert(['build','output'].includes(key)&&process.argv[i+1]&&!options.has(key));options.set(key,process.argv[i+1]);}
assert.equal(options.size,2,'Required: --build observer-build.json --output new-artifact-directory');
const output=resolve(root,options.get('output')),scope=relative(resolve(root,'artifacts/th14'),output);
assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope)&&!existsSync(output));
const disk=statfsSync(root);assert(disk.bavail*disk.bsize>=100*1024**3,'100 GiB free-space floor');
mkdirSync(output);
const sha=b=>createHash('sha256').update(b).digest('hex'),buildPath=resolve(root,options.get('build')),build=JSON.parse(read(buildPath));
for(const [name,digest]of Object.entries({...build.sourceHashes,...build.headerHashes}))assert.equal(sha(read(resolve(build.sourceSnapshotRoot,name))),digest,name);
for(const binding of build.objectBindings)assert.equal(sha(read(binding.path)),binding.sha256,binding.path);
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
assert.equal(sha(read(compiler)),build.compilerSha256);
const nativeTool=resolve(root,'tools/th14-spawn-beam-stack-native-v2-nov02.py'),nativePath=resolve(output,'native.json');
const python=process.env.TH_NATIVE_PYTHON||'py',pythonPrefix=process.env.TH_NATIVE_PYTHON?[]:['-3'];
const env={...process.env,TEMP:output,TMP:output};
execFileSync(python,[...pythonPrefix,'-X','utf8',nativeTool,'--output',nativePath],{cwd:root,env,windowsHide:true,stdio:'pipe',timeout:120000});
const native=JSON.parse(read(nativePath));assert.equal(native.toolSha256,sha(read(nativeTool)));assert.equal(native.cases.length,1536);
const fixture=resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-spawn-beam-stack-fixture-nov02.cpp'),wasmPath=resolve(output,'fixture.wasm');
execFileSync(compiler,[...build.flags,...build.linkFlags,fixture,...build.objectBindings.map(x=>x.path),'-o',wasmPath],{cwd:root,env,windowsHide:true,stdio:'pipe',timeout:120000});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),wasm=read(wasmPath);
const {instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;let count=0;
for(const row of native.cases){
 assert.equal(c.run(row.mode,row.duration,row.startZ,row.rate),0,JSON.stringify(row));
 const expected=[+row.vectorTemporaryWritten,row.wordRead.word,row.sampledZ,row.beamLength,row.beamLength];
 assert.deepEqual(Array.from({length:5},(_,i)=>c.word(i)>>>0),expected,JSON.stringify(row));count++;
}
const proof={passed:true,cases:count,all32InterpolationModes:true,
 actualCppEcl308AndAnmFactoryAndInterpreterAndBeamCallbackExecuted:true,
 actualOriginalVectorSamplerAndBeamCallbackExecuted:true,
 syntheticInitialVmAndStackInputsDeclared:true,nativeEclAndAllocationAndWholeGameNotExecuted:true,
 executableSha256:native.executableSha256,nativeProofSha256:sha(read(nativePath)),
 nativeToolSha256:sha(read(nativeTool)),fixtureSha256:sha(read(fixture)),checkerSha256:sha(read(new URL(import.meta.url))),
 wasmSha256:sha(wasm),engineBuildSha256:sha(read(buildPath)),engineObjectCount:build.objectBindings.length,
 sourceHashes:build.sourceHashes,headerHashes:build.headerHashes,
 nativeValuesProvidedToPortableEngine:false,completeGame:false,nativeEquivalent:false};
write(resolve(output,'verified.json'),JSON.stringify(proof,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:true,cases:count}));
