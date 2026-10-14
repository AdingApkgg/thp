// Future execution is explicit. Importing this file never starts a runtime.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const out=resolve(root,'artifacts/th14/startup-camera-same-input-math-prepared-oct14');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const pin=path=>{const bytes=readFileSync(path);return {path,bytes:bytes.length,sha256:sha(bytes)};};
function verify(binding){const bytes=readFileSync(binding.path);assert.equal(bytes.length,binding.bytes,binding.path);assert.equal(sha(bytes),binding.sha256,binding.path);return bytes;}

export async function executePreparedMathControl(){
  const plan=JSON.parse(readFileSync(resolve(out,'plan.json'),'utf8'));
  assert.equal(plan.schema,'th14-camera-same-input-math-plan-v1');
  assert.equal(plan.prepared,true);
  for(const binding of plan.requiredBindings)verify(binding);
  const input=JSON.parse(verify(plan.inputs).toString('utf8'));
  assert.equal(input.schema,'th14-original-camera-same-input-math-v1');
  assert.equal(input.cases.length,8);assert.equal(input.inputWords.length,96);assert.equal(input.oracleWords.length,128);
  assert.equal(input.declaredOriginalD3dxFpu.fpcw,0x37f);
  assert.equal(input.declaredOriginalD3dxFpu.nativeMeasured,false);
  assert.ok(!existsSync(plan.runDirectory),'new run directory required; preserve prior results');
  mkdirSync(plan.runDirectory);
  const env={...process.env,TEMP:plan.runDirectory,TMP:plan.runDirectory,TMPDIR:plan.runDirectory};
  // Only these two prepared C++ translation units; no old runner or production object.
  execFileSync(plan.compiler.path,plan.compilerArguments,{cwd:root,env,stdio:'inherit',windowsHide:true});
  const wasmPath=resolve(plan.runDirectory,'math.wasm'),bytes=readFileSync(wasmPath),module=await WebAssembly.compile(bytes);
  const imports=WebAssembly.Module.imports(module),exports=WebAssembly.Module.exports(module);
  assert.ok(imports.every(entry=>entry.module==='wasi_snapshot_preview1'),'unexpected host import');
  assert.ok(exports.every(entry=>!/(?:sdl|audio|th11|native|play)/i.test(entry.name)),'unexpected gameplay/device export');
  for(const name of plan.exportContract)assert.ok(exports.some(entry=>entry.name===name),'missing '+name);
  const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
  const instance=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
  const core=instance.exports,inputPointer=core.input_buffer()>>>0,outputPointer=core.output_buffer()>>>0;
  assert.equal(inputPointer%4,0);assert.equal(outputPointer%4,0);
  assert.ok(inputPointer+384<=core.memory.buffer.byteLength);assert.ok(outputPointer+512<=core.memory.buffer.byteLength);
  const view=new DataView(core.memory.buffer);
  input.inputWords.forEach((word,i)=>view.setUint32(inputPointer+i*4,word,true));
  assert.equal(core.run_math(),1);
  const output=Array.from({length:128},(_,i)=>new DataView(core.memory.buffer).getUint32(outputPointer+i*4,true));
  const packed=Buffer.alloc(512);output.forEach((word,i)=>packed.writeUInt32LE(word,i*4));
  const differences=[];
  output.forEach((word,index)=>{if(word!==input.oracleWords[index])differences.push({caseIndex:index>>>4,function:input.cases[index>>>4].function,matrixWordIndex:index&15,currentWord:word,originalD3dxWord:input.oracleWords[index]});});
  const outputPath=resolve(plan.runDirectory,'current-matrices.u32');writeFileSync(outputPath,packed,{flag:'wx'});
  const report={controlExecuted:true,comparisonPassed:differences.length===0,caseCount:8,comparedWords:128,differenceCount:differences.length,differences,outputWords:output,
    oracleInput:plan.inputs,plan:pin(resolve(out,'plan.json')),productionBindings:plan.productionBindings,fixture:pin(resolve(out,'fixture.cpp')),runner:pin(fileURLToPath(import.meta.url)),wasm:pin(wasmPath),imports,exports,output:pin(outputPath),
    declaredOriginalD3dxFpu:input.declaredOriginalD3dxFpu,executionCounts:{compiles:1,wasi:1,originalX86:0,nativeProcesses:0,browser:0,audio:0},productionChanged:false,nativeEquivalent:false,completeGame:false,
    scope:'Current frozen GraphicsMath LookAt/Perspective on exactly eight observed raw32 inputs compared with128 original pinned-D3DX output words. Declared original dispatch/FPCW37f versus portable WASI/libm; not a measured Native CPU overlay, SceneCompositor, Renderer/GPU or complete cold-start comparison.'};
  writeFileSync(resolve(plan.runDirectory,'report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({controlExecuted:true,comparisonPassed:report.comparisonPassed,differenceCount:report.differenceCount,report:resolve(plan.runDirectory,'report.json'),wasm:report.wasm}));
  return report;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv.length===3&&process.argv[2]==='--execute')await executePreparedMathControl();
  else if(process.argv.length===2)console.log('Prepared only. After review: node tools/th14-startup-camera-same-input-math-check.mjs --execute');
  else throw Error('Only explicit --execute is supported.');
}
