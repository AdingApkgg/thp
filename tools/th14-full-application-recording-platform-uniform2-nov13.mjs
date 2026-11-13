// Declared graphics boundary for CPU-only Application verification.
// The production renderer's new two-float uniform is validated, not rasterized.
import assert from 'node:assert/strict';
import {fullApplicationRecordingPlatform as prior} from './th14-full-application-recording-platform-texture-units-v2-nov07.mjs';
import {productionDeliveryServices} from './th14-production-delivery-services-nov13.mjs';
export function fullApplicationRecordingPlatform(module,memory,options){
 const platform=prior(module,memory,options);let calls=0,exports,asyncScheduled=0,asyncDelivered=0,nextFence=1;
 const fences=new Set(),extraCalls={};
 const count=name=>{extraCalls[name]=(extraCalls[name]??0)+1;};
 const delivery=productionDeliveryServices(memory,options.onAsyncError);
 Object.assign(platform.env,delivery.env);
 platform.closeServices=()=>delivery.close();
 const attach=platform.attach;
 platform.attach=value=>{exports=value;attach(value);};
 platform.env.th14_async_schedule_impl=(callback,data,delay)=>{
  assert(callback>0&&delay>=0&&delay<=60000);++asyncScheduled;
  const token=setTimeout(()=>{platform.timers.delete(token);try{exports.async_deliver_owned(callback,data);++asyncDelivered;}catch(e){options.onAsyncError?.(e);}},delay);
  platform.timers.add(token);
 };
 for(const name of ['glBlendFuncSeparate','glBlendEquationSeparate','glFlush'])platform.env[name]=(...args)=>{assert(args.every(Number.isFinite));count(name);};
 platform.env.glFenceSync=(condition,flags)=>{assert.equal(condition,0x9117);assert.equal(flags,0);const id=nextFence++;fences.add(id);count('glFenceSync');return id;};
 platform.env.glDeleteSync=id=>{if(id){assert(fences.delete(id));count('glDeleteSync');}};
 platform.env.glClientWaitSync=(id,flags)=>{assert(fences.has(id));assert.equal(flags,0);count('glClientWaitSync');return 0x911a;};
 if(WebAssembly.Module.imports(module).some(x=>x.module==='env'&&x.name==='glUniform2fv')){
  platform.env.glUniform2fv=(location,count,pointer)=>{
   assert(Number.isInteger(location)&&location>=0&&Number.isInteger(count)&&count>=0);
   assert(Number.isInteger(pointer)&&pointer>=0&&pointer+count*8<=memory.buffer.byteLength);
   new Float32Array(memory.buffer,pointer,count*2);++calls;
  };
 }
 const summary=platform.summary;
 platform.summary=()=>({...summary(),declaredUniform2Calls:calls,uniform2ValuesRangeChecked:true,productionDelivery:delivery.summary(),
  declaredAlreadySignaledGpuFences:true,liveDeclaredGpuFences:fences.size,extraCalls,ownedAsyncScheduled:asyncScheduled,ownedAsyncDelivered:asyncDelivered});
 return platform;
}
