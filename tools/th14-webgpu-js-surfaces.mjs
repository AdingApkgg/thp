// Original D3DX buffers versus actual C++ + Emscripten + JS WebGPU resample.
// A native JavaScript runtime supplies WebGPU; no browser, DOM or window.
const root=new URL('../',import.meta.url),args=new Map();for(let i=0;i<Deno.args.length;i+=2)args.set(Deno.args[i].slice(2),Deno.args[i+1]);
const dir=name=>{if(!args.get(name))throw Error('Missing --'+name);return new URL(args.get(name).replaceAll('\\','/').replace(/\/?$/,'/'),root);};
const home=dir('build'),reference=dir('reference'),out=dir('output');if(!out.href.startsWith(new URL('artifacts/th14/',root).href))throw Error('Private output required');
try{await Deno.stat(out);throw Error('Output exists');}catch(error){if(!(error instanceof Deno.errors.NotFound))throw error;}await Deno.mkdir(out,{recursive:true});
const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
const read=(base,path)=>Deno.readFile(new URL(path,base)),decode=bytes=>JSON.parse(new TextDecoder().decode(bytes));
const buildRaw=await read(home,'build.json'),build=decode(buildRaw);
for(const[path,row]of Object.entries(build.sourceBindings))if(await sha(await read(root,path))!==row.sha256)throw Error('Source changed '+path);
for(const[name,row]of Object.entries(build.sourceFiles))if(await sha(await read(home,'src/'+name))!==row.sha256)throw Error('Snapshot changed '+name);
const wasm=await read(home,'component.wasm');if(await sha(wasm)!==build.wasmSha256)throw Error('Wasm changed');
const nativeRaw=await read(reference,'native.json'),native=decode(nativeRaw),inputsRaw=await read(reference,'inputs.json'),inputs=decode(inputsRaw),source=await read(reference,'source.bgra');
if(await sha(source)!==inputs.sourceSha256||!native.sourceUploadReadbackByteExact||native.cases.length!==8)throw Error('Reference changed');
const {default:createModule}=await import(new URL('component.mjs',home)),{Th14WebGpuHost}=await import(new URL('Th14WebGpuHost.mjs',home)),{Th14WebGpuRuntime}=await import(new URL('Th14WebGpuRuntime.mjs',home));
const module=await createModule({wasmBinary:wasm,print:console.log,printErr:console.error});
const shader=new TextDecoder().decode(await read(home,'Th14WebGpu.wgsl')),resampleShader=new TextDecoder().decode(await read(home,'Th14WebGpuResample.wgsl'));
let host;module.th14WebGpuRuntime=new Th14WebGpuRuntime(module,{createHost:async()=>host=await Th14WebGpuHost.create({shader,resampleShader})});
const call=(name,...values)=>module.ccall(name,'number',values.map(()=> 'number'),values,{async:true});
const upload=raw=>{const pointer=module._gpu_allocate(raw.byteLength);if(!pointer)throw Error('Allocation failed');module.HEAPU8.set(new Uint8Array(raw.buffer,raw.byteOffset,raw.byteLength),pointer);return pointer;};
const words=values=>upload(Int32Array.from(values));
const surface=async(handle,width,height,format,raw,bpp)=>{if(await call('gpu_surface',handle,width,height,format,width*bpp,upload(raw),raw.length)!==1)throw Error('Surface rejected');};
const pixels=async(handle,size)=>{const pointer=await call('gpu_read',handle);return module.HEAPU8.slice(pointer,pointer+size);};
const equal=(a,b)=>a.length===b.length&&a.every((value,index)=>value===b[index]);
try{
  if(await call('gpu_initialize')!==1)throw Error('Initialize failed');await surface(1,640,480,1,source,4);
  const rows=[];
  for(const row of native.cases){
    const bpp=row.bpp,fill=inputs[bpp===2?'targetRgb565Prefill':'targetArgb8Prefill'],prefill=new Uint8Array(512*512*bpp);
    for(let i=0;i<prefill.length;++i)prefill[i]=(fill>>>(i%bpp*8))&255;
    await surface(2,512,512,bpp===2?3:1,prefill,bpp);
    if(await call('gpu_resample',1,words(row.sourceRect),2,words(row.destinationRect),0,0,0)!==1)throw Error('Resample rejected');
    const actual=await pixels(2,row.bytes),expected=await read(reference,row.pixelFile);if(await sha(expected)!==row.pixelSha256)throw Error('Native buffer changed');
    let differentBytes=0;for(let i=0;i<actual.length;++i)differentBytes+=+(actual[i]!==expected[i]);
    const result={index:row.index,name:row.name,bytes:actual.length,differentBytes,actualSha256:await sha(actual),nativeSha256:await sha(expected)};rows.push(result);console.log(JSON.stringify(result));await Deno.writeFile(new URL(`case-${row.index}.pixels`,out),actual);
  }
  const width=96,height=128,prefill=Uint8Array.from({length:width*height*4},(_,i)=>[0xa1,0xb2,0xc3,0xd4][i%4]),expected=prefill.slice();
  await surface(3,width,height,1,prefill,4);await call('gpu_clear',3,0xffa15127,words([3,7,49,61,47,43,90,119]),2);
  for(const[left,top,right,bottom]of [[3,7,49,61],[47,43,90,119]])for(let y=top;y<bottom;++y)for(let x=left;x<right;++x)expected.set([0x27,0x51,0xa1,0xff],(y*width+x)*4);
  const cleared=await pixels(3,expected.length);if(!equal(cleared,expected))throw Error('Partial clear mismatch');await Deno.writeFile(new URL('partial-clear.bgra',out),cleared);
  const pointer=await call('gpu_read',3),offset=(8*width+4)*4,replacement=new Uint8Array([0x22,0x55,0x77,0xff]);module.HEAPU8.set(replacement,pointer+offset);expected.set(replacement,offset);await call('gpu_dirty',3);
  await surface(4,width,height,1,prefill,4);await call('gpu_copy',3,words([4,8,39,51]),4,words([17,19]));
  const copied=prefill.slice();for(let y=0;y<43;++y)copied.set(expected.subarray(((8+y)*width+4)*4,((8+y)*width+39)*4),((19+y)*width+17)*4);
  const copiedActual=await pixels(4,copied.length);if(!equal(copiedActual,copied))throw Error('Version/copy mismatch');await Deno.writeFile(new URL('version-copy.bgra',out),copiedActual);await call('gpu_present',4);host.assertHealthy();
  const report={schema:'th14/emscripten-js-webgpu-surfaces/1',cases:8,exactCases:rows.filter(row=>!row.differentBytes).length,differentBytes:rows.reduce((sum,row)=>sum+row.differentBytes,0),rows,rectangleControls:{partialClearRectangles:2,cpuVersionInvalidation:true,copiedRectangleBytes:35*43*4,exact:true},
    actualCppRenderer:true,actualEmscriptenAsyncify:true,actualJavascriptWebgpuHost:true,wasmSha256:await sha(wasm),buildSha256:await sha(buildRaw),nativeReportSha256:await sha(nativeRaw),inputsSha256:await sha(inputsRaw),sourceSha256:await sha(source),toolSha256:await sha(await Deno.readFile(new URL(import.meta.url))),deno:Deno.version,
    browserRun:false,browserAcceptance:false,domCreated:false,osWindowCreated:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,scope:'Eight original D3DX HAL buffers and independent partial-clear/CPU-version/copy controls versus actual C++ Renderer, Emscripten Asyncify and JavaScript WebGPU host on a native runtime. No browser or ordinary UI acceptance.'};
  await Deno.writeTextFile(new URL('report.json',out),JSON.stringify(report,null,2)+'\n');if(report.exactCases!==8)Deno.exitCode=1;
}finally{host?.close();}
