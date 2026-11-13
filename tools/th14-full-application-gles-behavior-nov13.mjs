// Current quiet SDL/production worker services plus actual offscreen ANGLE.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-uniform2-nov13.mjs';
import {createTh14AngleContext} from './th14-node-sized-angle-context-nov12.mjs';
import {createTh14WasmGles} from './th14-node-wasm-gles-fences-nov12.mjs';
export function fullApplicationGlesPlatform(module,memory,options){
 const base=fullApplicationRecordingPlatform(module,memory,options);
 const context=createTh14AngleContext('C:/Users/APKGG/AppData/Local/Programs/Trae');
 try{
  const signatures=JSON.parse(readFileSync(resolve(import.meta.dirname,'../artifacts/th14/ui-replay-type0-gpu-nov09/gl-signatures.json')));
  // GLES3 gl31.h declarations, already exercised by the alpha-only GPU suite.
  signatures.glFlush={result:'void',args:[]};
  signatures.glUniform2fv={result:'void',args:['GLint','GLsizei','const GLfloat *']};
  const gpu=createTh14WasmGles(context,module,()=>memory,signatures);gpu.verifyFenceServices();Object.assign(base.env,gpu.env);
  const summary=base.summary;
  return {...base,readBGRA:()=>context.readBGRA(),getError:()=>context.getError(),
   closeGpu:()=>{const r=context.close();assert(r.every(x=>x.result===1));return r;},
   summary:()=>({...summary(),actualNativeGles:gpu.summary(),hardwarePixels:true,graphicsRecordingOnly:false,
    graphicsCompileAndLinkStatusDeclared:false,declaredAlphaQuantizer:null,declaredAlreadySignaledGpuFences:false,
    gpuContextClosed:context.closed,gpuContextCleanup:context.cleanup,audibleOutput:false})};
 }catch(e){context.close();throw e;}
}
