import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
// This is an Emscripten/JavaScript scheduling component, with no browser,
// window, renderer, OS input or audio device.
const root=resolve(import.meta.dirname,'..'),home=resolve(process.argv[2]);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const raw=readFileSync(resolve(home,'build.json')),build=JSON.parse(raw);
for(const [path,hash]of Object.entries(build.sourceBindings))assert.equal(sha(readFileSync(resolve(root,path))),hash,path);
const wasm=readFileSync(resolve(home,'component.wasm'));assert.equal(sha(wasm),build.wasmSha256);
const {default:createModule}=await import(pathToFileURL(resolve(home,'component.mjs')));
const {Th14WebGpuRuntime}=await import(pathToFileURL(resolve(root,'runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs')));
const module=await createModule({wasmBinary:wasm,print:()=>{},printErr:message=>{throw Error(message);}});
const timers=[],frames=[];
const runtime=new Th14WebGpuRuntime(module,{setTimer:callback=>timers.push(callback),requestFrame:callback=>frames.push(callback)});
module.th14WebGpuRuntime=runtime;
const core=runtime.bindCore({th11_key:module._th11_key});
const pointer=module._rng_async_status(),state=()=>Array.from(new Uint32Array(module.HEAPU8.buffer,pointer,32));
const rows=[];let release;
try{
 for(const bits of [16,32])for(let phase=0;phase<5;++phase)for(const locking of [0,1])for(const fail of [0,1])for(const visual of [0,1]){
  const args=[bits,phase,locking,fail,visual];module._rng_reference(...args);const expected=state();
  assert.equal(expected[1],0);assert.equal(expected[4],1);assert.equal(expected[15],fail);
  assert.equal(expected[3],10);assert.equal(expected[14],0);assert.equal(expected[17],2048);
  assert.equal(expected[22],1);assert.equal(expected[23],1);assert.equal(expected[24],1);
  let entered;const held=new Promise(resolve=>entered=resolve),gate=new Promise(resolve=>release=resolve);
  module.rngBoundaryWait=async()=>{entered();await gate;};
  module._rng_schedule(...args);assert.equal(timers.length,2);assert.equal(frames.length,1);
  timers.shift()();let timer;
  try{await Promise.race([held,new Promise((_,reject)=>timer=setTimeout(()=>reject(Error('Async boundary did not suspend')),5000))]);}finally{clearTimeout(timer);}
  const suspended=state();assert.equal(suspended[0],1);assert.equal(suspended[22],1);assert.equal(suspended[23],1);
  core.th11_key(17,1);timers.shift()();frames.shift()(12);
  await Promise.resolve();await Promise.resolve();assert.deepEqual(state(),suspended,'A queued callback entered the suspended C++ scope');
  assert.equal(runtime.pendingCallbacks,4);
  const previous=module.HEAPU8.buffer,bytes=previous.byteLength;
  module.rngTestMemory().grow(1);module.rngTestUpdateViews();
  assert.notEqual(module.HEAPU8.buffer,previous);assert.equal(module.HEAPU8.byteLength,bytes+65536);
  release();await runtime.tail;
  const actual=state();assert.deepEqual(actual,expected,JSON.stringify(args));
  assert.equal(runtime.failure,null);assert.equal(runtime.pendingCallbacks,0);assert.equal(timers.length,0);assert.equal(frames.length,0);
  rows.push({bits,phase,locking,fail,visual,actual,suspended,cppStackGuardWords:2048,growthBytes:65536});
 }
 assert.equal(rows.length,80);assert.equal(runtime.completedCallbacks,320);
 // An explicit isolated-unit negative control bypasses the production queue.
 // It must change the suspended state and leave the C++ ordering error visible.
 let entered;const held=new Promise(resolve=>entered=resolve),gate=new Promise(resolve=>release=resolve);
 module.rngBoundaryWait=async()=>{entered();await gate;};
 module._rng_schedule(32,3,1,0,0);timers.shift()();let timer;
 try{await Promise.race([held,new Promise((_,reject)=>timer=setTimeout(()=>reject(Error('Negative control did not suspend')),5000))]);}finally{clearTimeout(timer);}
 const negativeBefore=state();module._th11_key(17,1);const negativeDuring=state();
 assert.notDeepEqual(negativeDuring,negativeBefore);assert.equal(negativeDuring[1],1);
 release();await runtime.tail;timers.shift()();frames.shift()(12);await runtime.tail;
 const negativeAfter=state();assert.equal(negativeAfter[0],4);assert.equal(negativeAfter[1],1);assert.equal(negativeAfter[14],0);
 assert.equal(runtime.completedCallbacks,323);assert.equal(runtime.pendingCallbacks,0);
 const negativeControl={rawUnserializedKeyRejected:true,errors:1,before:negativeBefore,during:negativeDuring,after:negativeAfter};
 const report={schema:'th14/rng-async-scope/1',passed:true,cases:80,callbacks:320,
  actualCurrentCppRng:true,actualEmscriptenAsyncify:true,actualProductionCallbackQueue:true,
  nestedScopeRestored:true,recursiveObserverSuppressed:true,failureStateRetained:true,
  scriptAndVisualRngs:true,bothLockModes:true,allFiveBoundaries:true,
  cppStackGuardWordsPerCase:2048,memoryGrowthBytesPerCase:65536,
  buildSha256:sha(raw),wasmSha256:sha(wasm),checkerSha256:sha(readFileSync(import.meta.filename)),rows,negativeControl,
  browserRun:false,browserAcceptance:false,uiAcceptance:false,physicalAudioDevicesOpened:0,
  fullVmOrOriginalSchedulingAccepted:false,completeGame:false,nativeEquivalent:false,
  scope:'Production RngBoundaryScope and JavaScript callback queue across deliberate Emscripten Asyncify suspension at each RNG boundary. Checks nested and recursive observers, both lock modes, failure, stack guards, queued key/worker/frame order and memory growth against a synchronous execution. This is a scheduling component check; no browser, full VM update, native OS mutex or original thread timing is certified.'};
 writeFileSync(resolve(home,'verified.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({passed:true,cases:80,callbacks:320,cppStackGuardWordsPerCase:2048,browserAcceptance:false}));
}finally{release?.();}
