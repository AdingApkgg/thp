// Synthetic native OffscreenCanvas controls. No browser, DOM, window or retail
// input. Preserve both GPU bytes and PNG output, including codec differences.
import {Th14WebGpuHost} from '../runtimes/th12/portable/sdl/Th14WebGpuHost.mjs';
const root=new URL('../',import.meta.url),i=Deno.args.indexOf('--output');if(i<0||!Deno.args[i+1])throw Error('Missing --output');
const out=new URL(Deno.args[i+1].replaceAll('\\','/').replace(/\/?$/,'/'),root);if(!out.href.startsWith(new URL('artifacts/th14/',root).href))throw Error('Private output required');
try{await Deno.stat(out);throw Error('Output exists');}catch(error){if(!(error instanceof Deno.errors.NotFound))throw error;}await Deno.mkdir(out,{recursive:true});
const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
const shader=await Deno.readTextFile(new URL('runtimes/th12/portable/sdl/Th14WebGpu.wgsl',root)),resampleShader=await Deno.readTextFile(new URL('runtimes/th12/portable/sdl/Th14WebGpuResample.wgsl',root));
const source=new Uint8Array([0x22,0x55,0x77,255,1,2,3,255,0,255,0,255,255,0,0,255]),rows=[];
for(const format of ['bgra8unorm','rgba8unorm']){
 const canvas=new OffscreenCanvas(2,2),host=await Th14WebGpuHost.create({canvas,shader,resampleShader,gpu:{requestAdapter:options=>navigator.gpu.requestAdapter(options),getPreferredCanvasFormat:()=>format}});
 try{
  // COPY_SRC permits inspection; it does not change shader or color state.
  host.canvasContext.configure({device:host.device,format,alphaMode:'opaque',usage:GPUTextureUsage.RENDER_ATTACHMENT|GPUTextureUsage.COPY_SRC});
  host.upload(1,2,2,source);const texture=host.canvasContext.getCurrentTexture();host.present(1);const raw=await host.readTexture(texture,2,2);
  const expected=source.slice();if(format==='rgba8unorm')for(let at=0;at<expected.length;at+=4)[expected[at],expected[at+2]]=[expected[at+2],expected[at]];
  if(raw.some((v,index)=>v!==expected[index]))throw Error('GPU canvas bytes differ for '+format);
  const png=new Uint8Array(await(await canvas.convertToBlob({type:'image/png'})).arrayBuffer());
  await Deno.writeFile(new URL(format+'.raw',out),raw);await Deno.writeFile(new URL(format+'.png',out),png);
  rows.push({format,gpuBytes:raw.length,gpuRawSha256:await sha(raw),pngSha256:await sha(png),gpuBytesEqual:true});host.assertHealthy();
 }finally{host.close();}
}
const bindings={};for(const path of ['runtimes/th12/portable/sdl/Th14WebGpuHost.mjs','runtimes/th12/portable/sdl/Th14WebGpu.wgsl','runtimes/th12/portable/sdl/Th14WebGpuResample.wgsl'])bindings[path]=await sha(await Deno.readFile(new URL(path,root)));
const report={schema:'th14/native-webgpu-canvas-control/1',gpuPresentControlsPassed:true,rows,sourceBgra:[...source],copySrcUsageIntervention:true,opaque:true,
 deno:Deno.version,sourceBindings:bindings,toolSha256:await sha(await Deno.readFile(new URL(import.meta.url))),pngColorComparisonPending:true,
 browserRun:false,browserAcceptance:false,osWindowCreated:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,
 scope:'Two synthetic format controls of the actual JS host presentation shader and native OffscreenCanvas. Raw GPU storage is exact in each declared format. PNG exports retained for independent decoding; GPU bytes do not certify the PNG conversion or any browser compositor.'};
await Deno.writeTextFile(new URL('report.json',out),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({gpuPresentControlsPassed:true,formats:2,browserAcceptance:false}));
