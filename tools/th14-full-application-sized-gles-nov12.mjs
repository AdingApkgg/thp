// Real offscreen GPU execution with the existing quiet/local SDL services.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {fullApplicationRecordingPlatform} from './th14-full-application-recording-platform-texture-units-v2-nov07.mjs';
import {createTh14AngleContext} from './th14-node-sized-angle-context-nov12.mjs';
import {createTh14WasmGles} from './th14-node-wasm-gles-nov08.mjs';
const root=resolve(import.meta.dirname,'..');
export function fullApplicationGlesPlatform(module,memory,options){
 const base=fullApplicationRecordingPlatform(module,memory,options);
 const context=createTh14AngleContext(options.angleDirectory,options.renderWidth,options.renderHeight);
 const windowSizes=[];const originalSize=base.env.SDL_SetWindowSize;
 base.env.SDL_SetWindowSize=(id,width,height)=>{originalSize(id,width,height);windowSizes.push([width,height]);return 1;};
 try{
  const signatures=JSON.parse(readFileSync(resolve(root,'artifacts/th14/ui-replay-type0-gpu-nov09/gl-signatures.json')));
  const gpu=createTh14WasmGles(context,module,()=>memory,signatures);
  Object.assign(base.env,gpu.env);
  const originalSummary=base.summary;
  return{...base,gpu,context,readBGRA:()=>context.readBGRA(),getError:()=>context.getError(),
   closeGpu:()=>{const result=context.close();assert(result.every(r=>r.result===1));return result;},
   summary:()=>({...originalSummary(),hardwarePixels:true,graphicsRecordingOnly:false,
    graphicsCompileAndLinkStatusDeclared:false,declaredAlphaQuantizer:null,
    actualNativeGles:gpu.summary(),gpuContextClosed:context.closed,gpuContextCleanup:context.cleanup,
    originalSdlWindowIsDeclaredBoundary:true,requestedWindowSizes:windowSizes,audibleOutput:false})};
 }catch(e){context.close();throw e;}
}
