// Actual C++ Renderer/Asyncify Clear plus native WebGPU attachment probes.
const root=new URL('../',import.meta.url),args=new Map();
for(let i=0;i<Deno.args.length;i+=2)args.set(Deno.args[i].slice(2),Deno.args[i+1]);
const dir=name=>{if(!args.has(name))throw Error('Missing --'+name);return new URL(args.get(name).replaceAll('\\','/').replace(/\/?$/,'/'),root);};
const home=dir('build'),reference=dir('reference'),out=dir('output'),negative=args.get('expect-partial-rejection')==='true';
if(!out.href.startsWith(new URL('artifacts/th14/',root).href))throw Error('Private output required');
try{await Deno.stat(out);throw Error('Output exists');}catch(error){if(!(error instanceof Deno.errors.NotFound))throw error;}
await Deno.mkdir(out,{recursive:true});
const sha=async raw=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),v=>v.toString(16).padStart(2,'0')).join('');
const read=(base,path)=>Deno.readFile(new URL(path,base)),decode=raw=>JSON.parse(new TextDecoder().decode(raw));
const buildRaw=await read(home,'build.json'),build=decode(buildRaw),wasm=await read(home,'component.wasm');
if(await sha(wasm)!==build.wasmSha256)throw Error('Wasm changed');
for(const[path,row]of Object.entries(build.sourceBindings))if(await sha(await read(root,path))!==row.sha256)throw Error('Current source changed '+path);
for(const[path,row]of Object.entries(build.sourceFiles))if(await sha(await read(home,'src/'+path))!==row.sha256)throw Error('Frozen build changed '+path);
const referenceRaw=await read(reference,'report.json'),native=decode(referenceRaw);
if(native.caseCount!==96||!native.actualD3d9Hal||!native.allIndependentCpuExpectationsEqual)throw Error('Invalid HAL control');
if(native.toolSha256!==await sha(await read(root,'tools/th14-stencil-clear-hal-control.py')))throw Error('HAL source changed');
const {default:createModule}=await import(new URL('component.mjs',home));
const {Th14WebGpuHost}=await import(new URL('Th14WebGpuHost.mjs',home));
const {Th14WebGpuRuntime}=await import(new URL('Th14WebGpuRuntime.mjs',home));
const module=await createModule({wasmBinary:wasm,print:console.log,printErr:console.error});
let host;
module.th14WebGpuRuntime=new Th14WebGpuRuntime(module,{createHost:async()=>host=await Th14WebGpuHost.create({
  shader:new TextDecoder().decode(await read(home,'Th14WebGpu.wgsl')),resampleShader:new TextDecoder().decode(await read(home,'Th14WebGpuResample.wgsl'))})});
const call=(name,...values)=>module.ccall(name,'number',values.map(()=> 'number'),values,{async:true});
const upload=raw=>{const pointer=module._gpu_allocate(raw.byteLength);if(!pointer)throw Error('Allocation failed');module.HEAPU8.set(new Uint8Array(raw.buffer,raw.byteOffset,raw.byteLength),pointer);return pointer;};
const floatWord=value=>new Uint32Array(Float32Array.of(value).buffer)[0];
const clear=async(flags,color,depth,stencil,rects)=>{
  const raw=rects?Int32Array.from(rects.flat()):null,pointer=raw?upload(raw):0;
  try{if(await call('gpu_clear',flags,color,floatWord(depth),stencil,pointer,rects?.length??0)!==1)throw Error('C++ Clear failed');}
  finally{if(pointer)module._gpu_release(pointer);}
};
const pixels=async()=>{const pointer=await call('gpu_read');return module.HEAPU8.slice(pointer,pointer+native.width*native.height*4);};
const rows=[];let rejected=null;
try{
  if(await call('gpu_initialize')!==1)throw Error('C++ initialization failed');
  const probeShader=host.device.createShaderModule({code:`
@vertex fn vs(@builtin(vertex_index) id:u32)->@builtin(position) vec4f{let p=vec2f(f32((id<<1u)&2u),f32(id&2u));return vec4f(p*2.0-1.0,0.5,1);}
@fragment fn fs()->@location(0) vec4f{return vec4f(1);}`});
  const makeProbe=stencil=>host.device.createRenderPipeline({layout:'auto',vertex:{module:probeShader,entryPoint:'vs'},fragment:{module:probeShader,entryPoint:'fs',targets:[{format:'bgra8unorm'}]},
    depthStencil:{format:'depth24plus-stencil8',depthWriteEnabled:false,depthCompare:stencil?'always':'less',
      ...(stencil?{stencilFront:{compare:'equal'},stencilBack:{compare:'equal'},stencilReadMask:255,stencilWriteMask:0}:{})}});
  const stencilPipeline=makeProbe(true),depthPipeline=makeProbe(false);
  const probe=(stencil,ref)=>{
    const pass=host.commands().beginRenderPass({colorAttachments:[{view:host.target(1).createView(),loadOp:'load',storeOp:'store'}],depthStencilAttachment:host.depthAttachment(2)});
    pass.setPipeline(stencil?stencilPipeline:depthPipeline);if(stencil)pass.setStencilReference(ref);pass.draw(3);pass.end();host.resources.get(1).dirty=true;
  };
  for(const row of native.cases){
    await clear(7,0x7fb13257,.25,17,null);
    try{await clear(row.flags,0x7fa15327,.75,row.stencil,row.rectangles);}
    catch(error){if(!negative)throw error;if(!String(error).includes('Partial stencil clear'))throw error;rejected=String(error);break;}
    if(negative)throw Error('Expected the retained partial-stencil rejection');
    const buffers={color:await pixels()};
    for(const[ref,label]of[[row.stencil&255,'new-stencil'],[17,'old-stencil']]){
      await clear(1,0xff010203,0,0,null);probe(true,ref);buffers[label]=await pixels();
    }
    await clear(1,0xff030507,0,0,null);probe(false,0);buffers.depth=await pixels();
    const comparisons=[];
    for(const[label,raw]of Object.entries(buffers)){
      const expected=await read(reference,row.buffers[label].file);
      if(await sha(expected)!==row.buffers[label].sha256)throw Error('HAL buffer changed');
      let differentBytes=0;for(let i=0;i<raw.length;++i)differentBytes+=+(raw[i]!==expected[i]);
      await Deno.writeFile(new URL(`case-${String(row.index).padStart(3,'0')}-${label}.bgra`,out),raw);
      comparisons.push({label,bytes:raw.length,differentBytes,sha256:await sha(raw),halSha256:await sha(expected)});
    }
    rows.push({index:row.index,flags:row.flags,stencil:row.stencil,comparisons});
    if(row.index%24===23)console.log(JSON.stringify({cases:rows.length,differentBytes:rows.flatMap(r=>r.comparisons).reduce((n,r)=>n+r.differentBytes,0)}));
  }
  if(negative&&!rejected)throw Error('Missing expected rejection');
  host.assertHealthy();
  if(!negative)await call('gpu_close');
  const result={schema:'th14/cpp-js-webgpu-stencil-clear/1',negativeOnly:negative,rejected,caseCount:rows.length,rows,
    comparedBuffers:rows.reduce((n,r)=>n+r.comparisons.length,0),comparedBytes:rows.flatMap(r=>r.comparisons).reduce((n,r)=>n+r.bytes,0),
    differentBytes:rows.flatMap(r=>r.comparisons).reduce((n,r)=>n+r.differentBytes,0),
    actualCppRenderer:true,actualEmscriptenAsyncify:true,actualJavascriptWebgpuHost:true,actualNativeGpu:true,
    wasmSha256:await sha(wasm),buildSha256:await sha(buildRaw),halReportSha256:await sha(referenceRaw),toolSha256:await sha(await Deno.readFile(new URL(import.meta.url))),
    browserRun:false,browserAcceptance:false,visibleWindow:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,
    scope:'Actual C++ Renderer Clear through Asyncify and the JS host; own GPU stencil-equal/depth-less probes compare all buffers to96 independent D3D9 HAL controls. Native runtime only; no browser or original full-game proof.'};
  await Deno.writeTextFile(new URL('report.json',out),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({negativeOnly:negative,caseCount:result.caseCount,comparedBuffers:result.comparedBuffers,comparedBytes:result.comparedBytes,differentBytes:result.differentBytes,rejected}));
  if(!negative&&(result.caseCount!==96||result.differentBytes))Deno.exitCode=1;
}finally{host?.close();}
