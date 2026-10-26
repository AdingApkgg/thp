import {Th14WebGpuHost} from './Th14WebGpuHost.mjs';
import {bindTh14WebGpuCore} from './Th14WebGpuCore.mjs';

// Only one suspended Wasm stack may exist. Frame and loading callbacks share
// this queue; the next RAF is requested after the preceding callback returns.
export class Th14WebGpuRuntime {
  constructor(module,{createHost,requestFrame=globalThis.requestAnimationFrame?.bind(globalThis),setTimer=globalThis.setTimeout.bind(globalThis)}={}) {
    this.module=module;this.createHost=createHost??(()=>Th14WebGpuHost.create({canvas:module.canvas,onError:error=>this.fail(error)}));
    this.requestFrame=requestFrame;this.setTimer=setTimer;this.tail=Promise.resolve();this.failure=null;this.host=null;this.opening=null;
    this.completedCallbacks=0;this.pendingCallbacks=0;
  }
  fail(error) {if (!this.failure) {this.failure=error;this.module.onWebGpuError?.(error);}}
  run(action) {
    ++this.pendingCallbacks;
    const result=this.tail.then(()=>{if(this.failure)throw this.failure;return action();});
    this.tail=result.catch(error=>this.fail(error)).finally(()=>{--this.pendingCallbacks;++this.completedCallbacks;});
    return result;
  }
  async open() {
    if (!this.opening) this.opening=Promise.resolve().then(this.createHost).then(host=>this.host=host);
    await this.opening;
  }
  call(name,returnType,types,args) {return this.module.ccall(name,returnType,types,args,{async:true});}
  bindCore(raw) {return bindTh14WebGpuCore(this.module,raw);}
  schedule(callback,data,delay) {
    const deliver=()=>{void this.run(()=>this.call('th14_webgpu_invoke',null,['number','number'],[callback,data])).catch(()=>{});};
    if (delay<0) {
      if (!this.requestFrame) throw new Error('requestAnimationFrame unavailable');
      this.requestFrame(deliver);
    } else this.setTimer(deliver,delay);
  }
  startFrames(callback,data) {
    if (!this.requestFrame) throw new Error('requestAnimationFrame unavailable');
    const tick=time=>{
      void this.run(()=>this.call('th14_webgpu_frame','number',['number','number','number'],[callback,time,data]))
        .then(again=>{if(again&&!this.failure)this.requestFrame(tick);},()=>{});
    };
    return this.requestFrame(tick);
  }
}
