// Real Emscripten C++ callbacks suspend on an actual native WebGPU readback.
// The test controls only callback timing and release of the completed read.
const root=new URL('../',import.meta.url),get=name=>{const i=Deno.args.indexOf('--'+name);if(i<0||!Deno.args[i+1])throw Error('Missing --'+name);return new URL(Deno.args[i+1].replaceAll('\\','/').replace(/\/?$/,'/'),root);};
const home=get('build'),out=get('output');if(!out.href.startsWith(new URL('artifacts/th14/',root).href))throw Error('Private output required');
try{await Deno.stat(out);throw Error('Output exists');}catch(error){if(!(error instanceof Deno.errors.NotFound))throw error;}await Deno.mkdir(out,{recursive:true});
const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
const read=path=>Deno.readFile(new URL(path,home));
const buildRaw=await read('build.json'),build=JSON.parse(new TextDecoder().decode(buildRaw));
for(const [path,row]of Object.entries(build.sourceBindings))if(await sha(await Deno.readFile(new URL(path,root)))!==row.sha256)throw Error('Stale source '+path);
for(const [name,row]of Object.entries(build.sourceFiles))if(await sha(await read('src/'+name))!==row.sha256)throw Error('Changed frozen source '+name);
const {default:createModule}=await import(new URL('component.mjs',home)),{Th14WebGpuHost}=await import(new URL('Th14WebGpuHost.mjs',home)),{Th14WebGpuRuntime}=await import(new URL('Th14WebGpuRuntime.mjs',home));
const wasm=await read('component.wasm');if(await sha(wasm)!==build.wasmSha256)throw Error('Wasm mismatch');
const module=await createModule({wasmBinary:wasm,print:console.log,printErr:console.error});
const shader=new TextDecoder().decode(await read('Th14WebGpu.wgsl')),resampleShader=new TextDecoder().decode(await read('Th14WebGpuResample.wgsl'));
const timers=[],frames=[];let entered,release,host;
const readEntered=new Promise(resolve=>entered=resolve),readReleased=new Promise(resolve=>release=resolve);
const trace=[];
const runtime=new Th14WebGpuRuntime(module,{setTimer:callback=>timers.push(callback),requestFrame:callback=>frames.push(callback),createHost:async()=>{
  host=await Th14WebGpuHost.create({shader,resampleShader});
  const actualRead=host.read.bind(host);
  host.read=async handle=>{const bytes=await actualRead(handle);trace.push('gpu-read-complete');entered();await readReleased;trace.push('read-released');return bytes;};
  return host;
}});
module.th14WebGpuRuntime=runtime;
const check=(condition,message)=>{if(!condition)throw Error(message);};
try{
  check(await module.ccall('gpu_initialize','number',[],[],{async:true})===1,'C++ initialize failed');
  const pointer=module._gpu_status(),state=()=>Array.from(new Uint32Array(module.HEAPU8.buffer,pointer,12));
  module._gpu_start();check(timers.length===2&&frames.length===1,'Callback registration mismatch');
  timers.shift()();
  let timeout;await Promise.race([readEntered,new Promise((_,reject)=>{timeout=setTimeout(()=>reject(Error('Readback did not arrive')),5000);})]);clearTimeout(timeout);
  check(JSON.stringify(state())===JSON.stringify([1,7,0,0,0,0,0,0,0,0,0,0]),'First callback did not suspend at read');
  const core=runtime.bindCore({th11_key:module._th11_key});check(runtime.bindCore(core)===core,'Repeated launch wraps an already bound core');core.th11_key(17,1);
  timers.shift()();frames.shift()(10);
  const before=state();await Promise.resolve();await Promise.resolve();check(JSON.stringify(state())===JSON.stringify(before),'Queued C++ callback reentered suspended stack');
  const memory=module.th14TestMemory(),oldBuffer=module.HEAPU8.buffer,oldBytes=oldBuffer.byteLength;
  memory.grow(1);module.th14TestUpdateViews();check(module.HEAPU8.buffer!==oldBuffer&&module.HEAPU8.byteLength===oldBytes+65536,'Memory did not grow');
  release();await runtime.tail;
  check(JSON.stringify(state())===JSON.stringify([3,7,1,11,1,10,13,0,0,0,17,1]),'Worker/input/first frame order or C++ stack/pixels mismatch');
  for(const time of [20,30]){check(frames.length===1,'Missing next RAF');frames.shift()(time);await runtime.tail;}
  const final=state();check(JSON.stringify(final)===JSON.stringify([3,7,1,11,3,30,13,0,0,0,17,1]),'Final C++ callback state mismatch');
  check(frames.length===0&&timers.length===0&&runtime.pendingCallbacks===0&&runtime.completedCallbacks===6,'Callbacks did not retire');host.assertHealthy();
  const report={schema:'th14/emscripten-webgpu-async/1',passed:true,actualCppRenderer:true,actualEmscriptenAsyncify:true,actualJavascriptWebgpuHost:true,actualGpuReadback:true,
    readWasSuspended:true,noCallbackReentryWhileSuspended:true,wasmMemoryGrewDuringRead:true,growthBytes:65536,heapViewsReacquired:true,cppStackGuardWords:2048,
    realGpuPixelBytesCheckedInCpp:16,workerCallbacks:2,frameCallbacks:3,queuedKeyCalls:1,keyArguments:[17,1],coreBindingIdempotent:true,finalState:final,trace,wasmSha256:await sha(wasm),buildSha256:await sha(buildRaw),toolSha256:await sha(await Deno.readFile(new URL(import.meta.url))),deno:Deno.version,
    browserRun:false,browserAcceptance:false,domCreated:false,osWindowCreated:false,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false,
    scope:'Actual C++ Renderer clear/read and exported C++ callback trampolines in Emscripten Asyncify. A completed native WebGPU read is held while two callback kinds queue and Wasm memory grows. Checks the resumed 2048-word C++ stack, actual GPU bytes and callback order. Controlled callback timing only; no browser or ordinary UI acceptance.'};
  await Deno.writeTextFile(new URL('report.json',out),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cppStackGuardWords:2048,callbacks:6,memoryGrowthBytes:65536}));
}finally{release?.();host?.close();}
