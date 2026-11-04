import assert from 'node:assert/strict';
import {Th14AsyncRuntime} from '../runtimes/th12/portable/sdl/Th14AsyncRuntime.mjs';
const raf=[],timers=[],events=[];let resume,active=0,peak=0;
const module={ccall:async(name,type,types,args,options)=>{
  assert.equal(options.async,true);++active;peak=Math.max(peak,active);events.push(name);
  if(name==='th14_async_frame')await new Promise(resolve=>{resume=resolve;});
  --active;return name==='th14_async_frame'?args[2]:undefined;
}};
const runtime=new Th14AsyncRuntime(module,{requestFrame:callback=>(raf.push(callback),raf.length),setTimer:callback=>timers.push(callback)});
const flush=async()=>{for(let n=0;n<20;++n)await Promise.resolve();};
const raw={th11_key:()=>events.push('key'),th11_phase:()=>6},core=runtime.bindCore(raw);
assert.equal(core.th11_phase(),6);assert.equal(runtime.bindCore(core),core);
runtime.startFrames(11,1);assert.equal(raf.length,1);raf.shift()(123);await flush();
assert.deepEqual(events,['th14_async_frame']);assert.equal(raf.length,0);
runtime.schedule(12,0,0);timers.shift()();core.th11_key(1,1);await flush();
assert.deepEqual(events,['th14_async_frame']);assert.equal(runtime.pendingCallbacks,3);
resume();await flush();assert.deepEqual(events,['th14_async_frame','th14_async_invoke','key']);
assert.equal(peak,1);assert.equal(raf.length,1);assert.equal(runtime.pendingCallbacks,0);
// The resolved C++ false stops the chain; it is not replaced with a forced true.
runtime.startFrames(11,0);raf.pop()(456);await flush();resume();await flush();assert.equal(raf.length,1);
const failure=new Error('swap failed');let reported;
const failed=new Th14AsyncRuntime({ccall:()=>Promise.reject(failure)},{requestFrame:callback=>(raf.push(callback),1),onError:error=>reported=error});
failed.startFrames(1,1);raf.pop()(789);await flush();assert.equal(reported,failure);assert.equal(failed.failure,failure);
assert.equal(raf.length,1);assert.equal(failed.pendingCallbacks,0);
console.log(JSON.stringify({passed:true,suspendedFrameWaited:true,workerAndInputSerialized:true,falseStopsLoop:true,failureReported:true,peakConcurrentWasmCalls:peak}));
