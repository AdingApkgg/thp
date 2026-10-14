import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),out=resolve(root,'artifacts/th14/startup-camera-screen-correction-prepared-oct14');
const sha=b=>createHash('sha256').update(b).digest('hex');
const pin=path=>{const b=readFileSync(path);return {path,bytes:b.length,sha256:sha(b)};};
function verify(binding){const b=readFileSync(binding.path);assert.equal(b.length,binding.bytes,binding.path);assert.equal(sha(b),binding.sha256,binding.path);return b;}
const pack=words=>{const b=Buffer.alloc(words.length*4);words.forEach((v,i)=>b.writeUInt32LE(v,i*4));return b;};
export async function executePreparedScreenControl(){
 const plan=JSON.parse(readFileSync(resolve(out,'plan.json'),'utf8'));assert.equal(plan.schema,'th14-screen-correction-control-plan-v1');
 for(const b of plan.requiredBindings)verify(b);
 const input=JSON.parse(verify(plan.inputs).toString('utf8'));
 assert.equal(input.schema,'th14-screen-correction-control-input-v1');assert.equal(input.inputWords.length,32);assert.equal(input.oracleParameterWords.length,52);assert.equal(input.oracleMatrixWords.length,128);
 assert.equal(input.declaredOriginalD3dxFpu.fpcw,0x37f);assert.equal(input.declaredOriginalD3dxFpu.nativeMeasured,false);
 assert.ok(!existsSync(plan.runDirectory),'preserve all prior evidence; require a new run directory');mkdirSync(plan.runDirectory);
 const results=[];
 for(const build of plan.builds){
  const env={...process.env,TEMP:plan.runDirectory,TMP:plan.runDirectory,TMPDIR:plan.runDirectory};
  execFileSync(plan.compiler.path,build.compilerArguments,{cwd:root,env,stdio:'inherit',windowsHide:true});
  const bytes=readFileSync(build.wasmPath),module=await WebAssembly.compile(bytes),imports=WebAssembly.Module.imports(module),exports=WebAssembly.Module.exports(module);
  assert.ok(imports.every(x=>x.module==='wasi_snapshot_preview1'),'unexpected host import');
  assert.ok(exports.every(x=>!/(?:sdl|audio|th11|native|play)/i.test(x.name)),'unexpected runtime export');
  for(const name of plan.exports)assert.ok(exports.some(x=>x.name===name),'missing '+name);
  const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),instance=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
  const core=instance.exports,p=core.input_buffer()>>>0;assert.equal(p%4,0);assert.ok(p+128<=core.memory.buffer.byteLength);
  input.inputWords.forEach((v,i)=>new DataView(core.memory.buffer).setUint32(p+i*4,v,true));assert.equal(core.run_screen(),1,'real-math observer call count');
  const read=(pointer,count)=>{pointer>>>=0;assert.equal(pointer%4,0);assert.ok(pointer+count*4<=core.memory.buffer.byteLength);return Array.from({length:count},(_,i)=>new DataView(core.memory.buffer).getUint32(pointer+i*4,true));};
  const parameters=read(core.parameter_buffer(),52),matrices=read(core.matrix_buffer(),128),parameterDifferences=[],matrixDifferences=[];
  parameters.forEach((v,i)=>{if(v!==input.oracleParameterWords[i])parameterDifferences.push({camera:i/13|0,parameterWord:i%13,portWord:v,originalWord:input.oracleParameterWords[i]});});
  matrices.forEach((v,i)=>{if(v!==input.oracleMatrixWords[i])matrixDifferences.push({camera:i/32|0,matrix:i%32<16?'view':'projection',matrixWord:i%16,portWord:v,originalWord:input.oracleMatrixWords[i]});});
  const parameterPath=resolve(plan.runDirectory,build.mode+'-parameters.u32'),matrixPath=resolve(plan.runDirectory,build.mode+'-matrices.u32');
  writeFileSync(parameterPath,pack(parameters),{flag:'wx'});writeFileSync(matrixPath,pack(matrices),{flag:'wx'});
  results.push({mode:build.mode,parameters,matrices,parameterDifferenceCount:parameterDifferences.length,matrixDifferenceCount:matrixDifferences.length,parameterDifferences,matrixDifferences,wasm:pin(build.wasmPath),imports,exports,parameterOutput:pin(parameterPath),matrixOutput:pin(matrixPath)});
 }
 const after=results.find(x=>x.mode==='after');assert.ok(after);
 const report={controlExecuted:true,correctedParametersEqual:after.parameterDifferenceCount===0,correctedMatricesEqual:after.matrixDifferenceCount===0,comparisonPassed:after.parameterDifferenceCount===0&&after.matrixDifferenceCount===0,cameras:4,parameterWords:52,matrixWords:128,results,
  plan:pin(resolve(out,'plan.json')),inputs:plan.inputs,productionBindings:plan.productionBindings,fixture:pin(resolve(out,'fixture.cpp')),runner:pin(fileURLToPath(import.meta.url)),declaredOriginalD3dxFpu:input.declaredOriginalD3dxFpu,
  executionCounts:{compiles:2,wasi:2,originalX86:0,nativeProcesses:0,browser:0,audio:0},productionFilesChangedByRunner:0,productionObjectsRebuilt:0,nativeEquivalent:false,completeGame:false,
  scope:'Four direct calls to the real SceneCamera.screen() before and after one TH14-only production source correction, using original reset viewport fields and the fresh original D3DX FOV. Linker observers capture parameters then forward to unchanged real GraphicsMath. Before differences are retained; after52parameters/128matrix words compare against the declared pinned-D3DX FPCW37f baseline. No Native CPU, SceneCompositor construction, GPU/draw, other-title execution or complete-game1:1 claim.'};
 writeFileSync(resolve(plan.runDirectory,'report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({controlExecuted:true,comparisonPassed:report.comparisonPassed,results:results.map(x=>({mode:x.mode,parameterDifferences:x.parameterDifferenceCount,matrixDifferences:x.matrixDifferenceCount})),report:resolve(plan.runDirectory,'report.json')}));return report;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length===3&&process.argv[2]==='--execute')await executePreparedScreenControl();
 else if(process.argv.length===2)console.log('Prepared only. After review: node tools/th14-startup-camera-screen-correction-check.mjs --execute');
 else throw Error('Only explicit --execute is supported.');
}
