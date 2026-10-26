// Actual C++ Renderer/Asyncify versus canonical buffers from own D3D9+D3DX.
const root=new URL('../',import.meta.url),args=new Map();for(let i=0;i<Deno.args.length;i+=2)args.set(Deno.args[i].slice(2),Deno.args[i+1]);
const dir=name=>{if(!args.has(name))throw Error('Missing --'+name);return new URL(args.get(name).replaceAll('\\','/').replace(/\/?$/,'/'),root);};
const home=dir('build'),reference=dir('reference'),out=dir('output'),negative=args.get('expect-bgrx-rejection')==='true';
if(!out.href.startsWith(new URL('artifacts/th14/',root).href))throw Error('Private output required');
try{await Deno.stat(out);throw Error('Output exists');}catch(error){if(!(error instanceof Deno.errors.NotFound))throw error;}
await Deno.mkdir(out,{recursive:true});const tool=await Deno.readFile(new URL(import.meta.url));await Deno.writeFile(new URL('run-tool.mjs',out),tool);
const sha=async raw=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),v=>v.toString(16).padStart(2,'0')).join('');
const read=(base,path)=>Deno.readFile(new URL(path,base)),decode=raw=>JSON.parse(new TextDecoder().decode(raw));
const buildRaw=await read(home,'build.json'),build=decode(buildRaw),wasm=await read(home,'component.wasm');if(await sha(wasm)!==build.wasmSha256)throw Error('Wasm changed');
for(const[path,row]of Object.entries(build.sourceBindings))if(await sha(await read(root,path))!==row.sha256)throw Error('Current source changed '+path);
for(const[path,row]of Object.entries(build.sourceFiles))if(await sha(await read(home,'src/'+path))!==row.sha256)throw Error('Build snapshot changed '+path);
const nativeRaw=await read(reference,'report.json'),native=decode(nativeRaw);if(native.caseCount!==1344||!native.actualD3d9Hal||!native.actualD3dxFormatConversion)throw Error('Invalid reference');
if(native.toolSha256!==await sha(await read(root,'tools/th14-bgrx-raster-hal-control-oct27.py')))throw Error('HAL source changed');
const {default:createModule}=await import(new URL('component.mjs',home)),{Th14WebGpuHost}=await import(new URL('Th14WebGpuHost.mjs',home)),{Th14WebGpuRuntime}=await import(new URL('Th14WebGpuRuntime.mjs',home));
const errors=[];const module=await createModule({wasmBinary:wasm,print:console.log,printErr:value=>{errors.push(String(value));console.error(value);}});let host;
module.th14WebGpuRuntime=new Th14WebGpuRuntime(module,{createHost:async()=>host=await Th14WebGpuHost.create({shader:new TextDecoder().decode(await read(home,'Th14WebGpu.wgsl')),resampleShader:new TextDecoder().decode(await read(home,'Th14WebGpuResample.wgsl'))})});
const call=(name,...values)=>module.ccall(name,'number',values.map(()=> 'number'),values,{async:true});
const clear=async(color,rects)=>{const words=rects?Int32Array.from(rects.flat()):null,pointer=words?module._gpu_allocate(words.byteLength):0;if(words)module.HEAPU8.set(new Uint8Array(words.buffer),pointer);try{if(await call('gpu_clear',color,pointer,rects?.length??0)!==1)throw Error('C++ clear rejected');}finally{if(pointer)module._gpu_release(pointer);}};
const pixels=async()=>{const pointer=await call('gpu_read');if(!pointer)throw Error('C++ read rejected');return module.HEAPU8.slice(pointer,pointer+16*16*4);};
const blend=async(enabled,s,d,op,mask)=>{if(await call('gpu_blend',+enabled,s,d,op,mask)!==1)throw Error('C++ blend rejected');};
const rows=[];let rejection=null;
try{
 if(await call('gpu_initialize')!==1)throw Error('Initialize failed');
 for(const row of negative?[native.cases.find(row=>row.format===22)]:native.cases){
  try{
   if(await call('gpu_case',row.format)!==1)throw Error('Case rejected');
   await blend(false,2,1,1,row.colorMask);await clear(row.clearColor,null);await clear(row.partialColor,row.rectangles);
  }catch(error){if(!negative||!errors.some(line=>line.includes('WebGPU packed raster target unsupported')))throw error;rejection=String(error);break;}
  if(negative)throw Error('Missing expected BGRX rejection');
  const buffers={clear:await pixels()};await blend(row.blendEnabled,row.sourceBlend,row.destinationBlend,row.blendOperation,row.colorMask);
  if(await call('gpu_draw',row.sourceColor,0,0,16,16)!==1)throw Error('Draw rejected');buffers.first=await pixels();
  await blend(true,7,8,1,15);if(await call('gpu_draw',0x6b27a1d3,4,5,14,15)!==1)throw Error('Chain draw rejected');buffers.chain=await pixels();
  const comparisons=[];
  for(const[label,raw]of Object.entries(buffers)){
   const expected=await read(reference,row.buffers[label].file);if(await sha(expected)!==row.buffers[label].sha256)throw Error('Canonical reference changed');
   let differentBytes=0;for(let i=0;i<raw.length;++i)differentBytes+=+(raw[i]!==expected[i]);
   const file=`case-${String(row.index).padStart(4,'0')}-${label}.bgra`;await Deno.writeFile(new URL(file,out),raw);comparisons.push({label,file,bytes:raw.length,differentBytes,sha256:await sha(raw),halSha256:await sha(expected)});
  }
  rows.push({index:row.index,format:row.format,comparisons});if(rows.length%224===0)console.log(JSON.stringify({cases:rows.length,differentBytes:rows.flatMap(r=>r.comparisons).reduce((n,r)=>n+r.differentBytes,0)}));
 }
 if(negative&&!rejection)throw Error('Expected rejection not observed');host.assertHealthy();if(!negative)await call('gpu_close');
 const report={schema:'th14/cpp-js-bgrx-raster/1',negativeOnly:negative,rejection,errors,caseCount:rows.length,rows,comparedBuffers:rows.length*3,
  comparedBytes:rows.length*3*1024,differentBytes:rows.flatMap(row=>row.comparisons).reduce((n,row)=>n+row.differentBytes,0),
  actualCppRenderer:true,actualEmscriptenAsyncify:true,actualJavascriptWebgpuHost:true,actualNativeGpu:true,referenceIsActualD3dxCanonicalConversion:true,
  wasmSha256:await sha(wasm),buildSha256:await sha(buildRaw),nativeReportSha256:await sha(nativeRaw),toolSha256:await sha(tool),
  browserRun:false,browserAcceptance:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,
  scope:'Actual Renderer A8/X8 Clear and two draw/read passes versus own D3D9 HAL buffers converted to canonical A8 by real D3DX. Raw X8 ignored-byte buffers are separately retained by the oracle. No dropped-channel comparison, browser, original ordinary UI or whole-game acceptance.'};
 await Deno.writeTextFile(new URL('report.json',out),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({negativeOnly:negative,caseCount:report.caseCount,comparedBuffers:report.comparedBuffers,comparedBytes:report.comparedBytes,differentBytes:report.differentBytes,rejection}));
 if(!negative&&(report.caseCount!==1344||report.differentBytes))Deno.exitCode=1;
}finally{host?.close();}
