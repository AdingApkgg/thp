import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-texture-units-v2-nov07.mjs';
import {createTh14AngleContext} from './th14-node-sized-angle-context-nov12.mjs';
import {createTh14WasmGles} from './th14-node-wasm-gles-fences-nov12.mjs';

const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/helper-clear-oracle-nov13');
const load=p=>JSON.parse(readFileSync(p)),sha=b=>createHash('sha256').update(b).digest('hex');
const executedDriver=readFileSync(import.meta.filename),driverSha256=sha(executedDriver);
const variant='candidate';
const attempt='v4';
const clearOnly=process.argv.includes('--clear-only');
const traceEnabled=process.argv.includes('--trace');
const B=resolve(R,'artifacts/th14/alpha-range-current-nov13'),O=resolve(B,traceEnabled?'gpu-clear-trace':clearOnly?'gpu-clears':'gpu');mkdirSync(O);
writeFileSync(resolve(O,'executed-driver.mjs'),executedDriver);
const build=load(resolve(B,'build.json')),bytes=readFileSync(resolve(B,'probe.wasm'));
assert.equal(sha(bytes),build.wasmSha256);assert(build.explicitTh14Branch);
for(const [name,digest]of Object.entries({...build.sourceBindings,...build.generatedSourceBindings}))assert.equal(sha(readFileSync(resolve(R,name))),digest,name);
const refs=[false,true].map(low=>{
 const dir=resolve(R,low?'artifacts/th14/gpu-alpha-low':'artifacts/th14/gpu-alpha');
 const manifest=load(resolve(dir,'native.json')),pixels=readFileSync(resolve(dir,'native.bgra'));
 assert.equal(manifest.generated,true);assert.equal(manifest.lowAlpha,low);assert.equal(manifest.cases.length,4096);
 assert.equal(sha(pixels),manifest.pixelsSha256);assert.equal(pixels.length,4096*4096);
 for(let i=0;i<4096;i++)assert.equal(sha(pixels.subarray(i*4096,(i+1)*4096)),manifest.cases[i].pixelsSha256);
 return{manifest,pixels,manifestSha256:sha(readFileSync(resolve(dir,'native.json')))};
});
const module=await WebAssembly.compile(bytes),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const base=fullApplicationRecordingPlatform(module,memory,{clockInput:0,archivePath:'',fontDirectory:'',saveDirectory:O});
const context=createTh14AngleContext('C:/Users/APKGG/AppData/Local/Programs/Trae');
const signatures=load(resolve(R,'artifacts/th14/ui-replay-type0-gpu-nov09/gl-signatures.json'));
// Khronos GLES3 gl31.h, explicit additions required by this production branch.
Object.assign(signatures,{
 glFlush:{result:'void',args:[]},
 glUniform2fv:{result:'void',args:['GLint','GLsizei','const GLfloat *']},
 glIsEnabled:{result:'GLboolean',args:['GLenum']},
});
let gpu,c,created=false,closed=false,exception=null,alphaCases=0,differentAlphaCases=0,differentAlphaPixels=0,clearCases=0,differentClearCases=0;
const firstDifferences=[],clearRows=[],alphaHashes=[],clears=[],began=performance.now();
let tracedCase=-1;const trace=[];
try{
 gpu=createTh14WasmGles(context,module,()=>memory,signatures,(name,args)=>{
  if(traceEnabled&&[24,25].includes(tracedCase)&&name!=='shader-source-content')trace.push({case:tracedCase,name,args});
 });gpu.verifyFenceServices();
 const wasi=new WASI({version:'preview1',args:[],env:{}});
 const instance=await WebAssembly.instantiate(module,{env:{...base.env,...gpu.env},wasi_snapshot_preview1:wasi.wasiImport});
 c=instance.exports;base.attach(c);wasi.initialize(instance);
 assert.equal(c.gpu_initialize(),1);created=true;assert.equal(context.getError(),0);
 const image=ptr=>{assert(ptr>0);return Buffer.from(new Uint8Array(memory.buffer,ptr,4096));};
 const delta=(a,b)=>{assert.equal(a.length,b.length);let count=0;for(let i=0;i<a.length;i+=4)if(a.readUInt32LE(i)!==b.readUInt32LE(i))count++;return count;};
 for(let low=0;low<(clearOnly?0:2);low++){
  c.gpu_alpha_texture(low);const aggregate=createHash('sha256');
  for(let i=0;i<4096;i++){
   const row=refs[low].manifest.cases[i],actual=image(c.gpu_alpha_case(row.operation,row.compare,row.reference));
   const expected=refs[low].pixels.subarray(i*4096,(i+1)*4096),different=delta(actual,expected);
   aggregate.update(actual);alphaCases++;differentAlphaPixels+=different;
   if(different){differentAlphaCases++;if(firstDifferences.length<16)firstDifferences.push({suite:'alpha',low,...row,differentPixels:different,actualSha256:sha(actual)});}
   assert.equal(context.getError(),0);
  }
  alphaHashes.push({low:!!low,actualSha256:aggregate.digest('hex'),nativeSha256:sha(refs[low].pixels),nativeManifestSha256:refs[low].manifestSha256});
 }
}catch(e){exception=String(e?.stack??e);}
finally{
 if(created)try{c.gpu_close();closed=true;}catch(e){exception??=String(e?.stack??e);}
 try{context.close();}catch(e){exception??=String(e?.stack??e);}
}
const platform=base.summary(),report={variant,wasmSha256:build.wasmSha256,driverSha256,
 alphaCases,differentAlphaCases,differentAlphaPixels,alphaHashes,clearCases,differentClearCases,clearRows,firstDifferences,
 exception,closed,gpuContextClosed:context.closed,gpuCleanup:context.cleanup,gpu:gpu?.summary(),
 platform:{pendingTimers:platform.pendingTimers,openFiles:platform.openFiles,window:platform.window,context:platform.context,stream:platform.stream,audioBytes:platform.audioBytes},
 actualGles:true,browserUsed:false,audibleOutput:false,elapsedSeconds:(performance.now()-began)/1000,
 originalAlphaReferenceReused:true,newOriginalGameRuns:0,newNativeClearOracle:false,fullFramesOrRngAccepted:false,completeGame:false};
writeFileSync(resolve(O,'report.json'),JSON.stringify(report,null,2)+'\n');
writeFileSync(resolve(O,'clears.bgra'),Buffer.concat(clears));
if(traceEnabled)writeFileSync(resolve(O,'trace.json'),JSON.stringify(trace,null,2)+'\n');
console.log(JSON.stringify({variant,alphaCases,differentAlphaCases,differentAlphaPixels,clearCases,differentClearCases,exception,closed,seconds:report.elapsedSeconds,firstDifferences:firstDifferences.slice(0,2)}));
assert.equal(exception,null);assert.equal(alphaCases,clearOnly?0:8192);assert.equal(clearCases,0);assert(closed&&context.closed);
assert(Object.values(report.gpu.liveObjects).every(n=>n===0));
assert(Object.values(report.platform).every(n=>n===0));
assert.equal(differentAlphaPixels,0);assert.equal(differentClearCases,0);
