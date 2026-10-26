// Native JavaScript/WebGPU + actual Emscripten C++ component. No browser,
// DOM, OS window, application input, audio or UI automation is used.
const root=new URL('../',import.meta.url);
const options=new Map();
for(let i=0;i<Deno.args.length;i+=2){if(!Deno.args[i].startsWith('--')||!Deno.args[i+1])throw Error('Expected --name value');options.set(Deno.args[i].slice(2),Deno.args[i+1]);}
const directory=name=>{const value=options.get(name);if(!value)throw Error(`Missing --${name}`);return new URL((/^[A-Za-z]:[\\/]/.test(value)?'file:///':'')+value.replaceAll('\\','/').replace(/\/?$/,'/'),root);};
const buildHome=directory('build'),reference=directory('reference'),out=directory('output');
if(!out.href.startsWith(new URL('artifacts/th14/',root).href))throw Error('Output must be private TH14 artifacts');
try{await Deno.stat(out);throw Error('Output already exists');}catch(error){if(!(error instanceof Deno.errors.NotFound))throw error;}
await Deno.mkdir(out,{recursive:true});
const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
const read=async(base,name)=>new Uint8Array(await Deno.readFile(new URL(name,base)));
const json=async(base,name)=>JSON.parse(new TextDecoder().decode(await read(base,name)));
const equal=(a,b)=>a.length===b.length&&a.every((value,index)=>value===b[index]);
const buildRaw=await read(buildHome,'build.json'),build=JSON.parse(new TextDecoder().decode(buildRaw));
if(!build.actualCppRenderer||!build.asyncify||build.browserRun)throw Error('Unexpected component build');
for(const [path,binding]of Object.entries(build.sourceBindings)){const raw=await read(root,path);if(raw.length!==binding.bytes||await sha(raw)!==binding.sha256)throw Error(`Stale source ${path}`);}
const wasm=await read(buildHome,'component.wasm');if(await sha(wasm)!==build.wasmSha256||await sha(await read(buildHome,'component.mjs'))!==build.loaderSha256)throw Error('Build hash mismatch');
const preparedRaw=await read(reference,'prepared.json'),prepared=JSON.parse(new TextDecoder().decode(preparedRaw)),nativeRaw=await read(reference,'native.json'),native=JSON.parse(new TextDecoder().decode(nativeRaw)),original=await read(reference,'native.bgra');
if(await sha(original)!==native.pixelsSha256||prepared.frames.length!==21)throw Error('Invalid retained reference');
const {default:createModule}=await import(new URL('component.mjs',buildHome));
const {Th14WebGpuHost}=await import(new URL('Th14WebGpuHost.mjs',buildHome));
const {Th14WebGpuRuntime}=await import(new URL('Th14WebGpuRuntime.mjs',buildHome));
const module=await createModule({wasmBinary:wasm,noInitialRun:true,print:console.log,printErr:console.error});
const shader=new TextDecoder().decode(await read(buildHome,'Th14WebGpu.wgsl')),resampleShader=new TextDecoder().decode(await read(buildHome,'Th14WebGpuResample.wgsl'));
let host,adapterInfo;const calls={};
const runtime=new Th14WebGpuRuntime(module,{createHost:async()=>{
  const adapter=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});if(!adapter)throw Error('No native WebGPU adapter');
  adapterInfo=Object.fromEntries(['vendor','architecture','device','description','subgroupMinSize','subgroupMaxSize'].map(key=>[key,adapter.info[key]]));
  const device=await adapter.requestDevice({requiredFeatures:[]});host=new Th14WebGpuHost(device,shader,resampleShader);
  for(const name of ['upload','depth','draw','clear','copy','resample','read','present','release']){const original=host[name].bind(host);host[name]=(...args)=>{calls[name]=(calls[name]??0)+1;return original(...args);};}
  await host.initialize();return host;
}});
module.th14WebGpuRuntime=runtime;
const call=(name,...args)=>module.ccall(name,'number',args.map(()=> 'number'),args,{async:true});
const upload=bytes=>{const pointer=module._gpu_allocate(bytes.length);if(!pointer)throw Error('Allocation failed');module.HEAPU8.set(bytes,pointer);return pointer;};
const words=async(values,action)=>{const raw=Uint32Array.from(values),pointer=upload(new Uint8Array(raw.buffer));try{return await action(pointer);}finally{module._gpu_release(pointer);}};
try{
  if(await call('gpu_initialize')!==1)throw Error('C++ Renderer initialization failed');
  for(const texture of prepared.textures){const raw=await read(reference,texture.file);if(await sha(raw)!==texture.sha256)throw Error('Texture hash mismatch');const pointer=upload(raw);if(await call('gpu_texture',texture.handle,texture.width,texture.height,texture.format,texture.pitch,pointer,raw.length)!==1)throw Error('C++ texture rejected');}
  const execute=async command=>{
    let ok;
    switch(command.kind){
      case 'renderState':ok=await call('gpu_render_state',command.key,command.value);break;
      case 'samplerState':ok=await call('gpu_sampler',command.sampler,command.key,command.value);break;
      case 'textureStageState':ok=await call('gpu_texture_stage',command.stage,command.key,command.value);break;
      case 'texture':ok=await call('gpu_bind',command.sampler,command.handle);break;
      case 'fvf':ok=await call('gpu_fvf',command.value);break;
      case 'transform':ok=await words(command.words,pointer=>call('gpu_matrix',command.key,pointer));break;
      case 'viewport':ok=await words(command.words,pointer=>call('gpu_viewport',pointer));break;
      case 'clear':ok=await words(command.rectangles,pointer=>call('gpu_clear',command.flags,command.color,command.depthWord,command.stencil,pointer,command.rectangles.length/4));break;
      case 'draw':ok=await words(command.words,pointer=>call('gpu_draw',command.topology,command.count,command.stride,pointer));break;
      case 'controlledScreenQueue':case 'controlledScreenFlush':ok=1;break;
      default:throw Error(`Unknown command ${command.kind}`);
    }
    if(ok!==1)throw Error(`C++ command rejected: ${command.kind}`);
  };
  const rows=[];
  for(const frame of prepared.frames){
    if(await call('gpu_begin')!==1)throw Error('C++ frame initialization failed');
    for(const command of [...frame.initialState,...frame.commands])await execute(command);
    const pointer=await call('gpu_read');if(!pointer)throw Error('C++ readback failed');
    const actual=module.HEAPU8.slice(pointer,pointer+640*480*4),n=native.frames.find(row=>row.stage===frame.stage&&row.frame===frame.frame),expected=original.subarray(n.offset,n.offset+n.bytes);
    if(await sha(expected)!==n.sha256||actual.length!==expected.length)throw Error('Native buffer invalid');
    let differentBytes=0;for(let i=0;i<actual.length;++i)differentBytes+=+(actual[i]!==expected[i]);
    const row={stage:frame.stage,frame:frame.frame,bytes:actual.length,differentBytes,actualSha256:await sha(actual),nativeSha256:await sha(expected)};rows.push(row);
    await Deno.writeFile(new URL(`stage${frame.stage}-frame${frame.frame}.bgra`,out),actual);console.log(JSON.stringify(row));host.assertHealthy();
  }
  const report={schema:'th14/emscripten-js-webgpu-stage/1',frames:rows.length,exactFrames:rows.filter(row=>!row.differentBytes).length,differentBytes:rows.reduce((sum,row)=>sum+row.differentBytes,0),rows,actualCppRenderer:true,actualEmscriptenAsyncify:true,actualJavascriptWebgpuHost:true,
    deno:Deno.version,adapterInfo,requiredFeatures:[],gpuCalls:calls,wasmSha256:build.wasmSha256,buildSha256:await sha(buildRaw),preparedSha256:await sha(preparedRaw),nativeReportSha256:await sha(nativeRaw),nativePixelsSha256:await sha(original),toolSha256:await sha(await Deno.readFile(new URL(import.meta.url))),
    browserRun:false,browserAcceptance:false,domCreated:false,osWindowCreated:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,
    scope:'Actual C++ Renderer and Emscripten Asyncify bridge execute the JavaScript WebGPU host on a native runtime with declared SDL lifetime shim. Full retained Stage buffers are compared with unchanged controlled screen-queue exclusions. No browser, ordinary UI, DOM, real SDL window, physical input/audio, presentation compositor or complete-game acceptance.'};
  await Deno.writeTextFile(new URL('report.json',out),JSON.stringify(report,null,2)+'\n');
  if(report.exactFrames!==21)Deno.exitCode=1;
}finally{host?.close();}
