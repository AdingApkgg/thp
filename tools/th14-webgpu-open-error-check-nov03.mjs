// A failed WebGPU host initialization must notify the parent exactly once.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {Th14WebGpuRuntime} from '../runtimes/th12/portable/sdl/Th14WebGpuRuntime.mjs';

for(const failure of [new Error('No WebGPU adapter'),new Error('requestDevice rejected')]) {
  let calls=0;const notifications=[];
  const runtime=new Th14WebGpuRuntime({onWebGpuError:error=>notifications.push(error)},
    {createHost:async()=>{calls++;throw failure;}});
  const outcomes=await Promise.allSettled([runtime.open(),runtime.open()]);
  assert.equal(calls,1);assert.deepEqual(outcomes.map(x=>x.status),['rejected','rejected']);
  assert(outcomes.every(x=>x.reason===failure));assert.deepEqual(notifications,[failure]);
  assert.equal(runtime.failure,failure);assert.equal(runtime.host,null);
  await assert.rejects(runtime.run(()=>{throw new Error('must not run');}),error=>error===failure);
  await runtime.tail;assert.deepEqual(notifications,[failure]);
}
{
  const host={name:'synthetic host'},notifications=[];let calls=0;
  const runtime=new Th14WebGpuRuntime({onWebGpuError:error=>notifications.push(error)},
    {createHost:async()=>{calls++;return host;}});
  await Promise.all([runtime.open(),runtime.open()]);
  assert.equal(calls,1);assert.equal(runtime.host,host);assert.equal(runtime.failure,null);
  assert.equal(await runtime.run(()=>42),42);await runtime.tail;assert.deepEqual(notifications,[]);
}
{
  let library,closed=0;const error=new Error('No WebGPU adapter'),notifications=[];
  const module={onWebGpuError:e=>notifications.push(e)};
  module.th14WebGpuRuntime=new Th14WebGpuRuntime(module,{createHost:async()=>{throw error;}});
  const heap=new Float32Array(8);
  runInNewContext(readFileSync(new URL('../runtimes/th12/portable/sdl/Th14WebGpuLibrary.js',import.meta.url),'utf8'),
    {addToLibrary:value=>{library=value;},Module:module,HEAPF32:heap});
  assert.equal(await library.th14_webgpu_open(0),0);assert.deepEqual(notifications,[error]);
  assert.doesNotThrow(()=>library.th14_webgpu_close());
  delete module.th14WebGpuRuntime;assert.doesNotThrow(()=>library.th14_webgpu_close());
  module.th14WebGpuRuntime=new Th14WebGpuRuntime(module,{createHost:async()=>({alphaBoundaries:new Float32Array([.25,.5]),close:()=>closed++})});
  assert.equal(await library.th14_webgpu_open(0),1);assert.deepEqual(Array.from(heap.slice(0,2)),[.25,.5]);
  library.th14_webgpu_close();assert.equal(closed,1);
}
console.log(JSON.stringify({failedInitializationNotifications:2,concurrentOpenCreatesOnce:true,queuedWorkRejected:true,failedBridgeReturnsZero:true,failedCloseIsSafe:true,successfulInitializationUnaffected:true}));
