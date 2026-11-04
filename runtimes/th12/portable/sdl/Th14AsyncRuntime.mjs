// SDL's WebGL swap can suspend through Asyncify. A raw RAF callback sees the
// unwind return, not the eventual C++ result. Own every callback stack with an
// async ccall and serialize mutations until that stack has finished.
const queuedVoid=new Set(['th11_key','th11_keys_clear','th11_music_enabled',
  'th11_loop_start','th11_loop_stop','th11_loop_pause','th11_touch','th11_touch_cancel',
  'th11_touch_options','th11_touch_controls','th11_touch_stick','sdl_loop_pause',
  'sdl_touch','sdl_touch_cancel','sdl_touch_options','sdl_touch_gestures','sdl_touch_mode','sdl_touch_controls']);

export class Th14AsyncRuntime {
  constructor(module,{requestFrame=globalThis.requestAnimationFrame?.bind(globalThis),setTimer=globalThis.setTimeout.bind(globalThis),onError=error=>module.onAsyncError?.(error)}={}) {
    this.module=module;this.requestFrame=requestFrame;this.setTimer=setTimer;this.onError=onError;
    this.tail=Promise.resolve();this.failure=null;this.pendingCallbacks=0;this.completedCallbacks=0;
    this.boundCores=new WeakSet();
  }
  fail(error) {if(!this.failure){this.failure=error;this.onError(error);}}
  run(action) {
    ++this.pendingCallbacks;
    const result=this.tail.then(()=>{if(this.failure)throw this.failure;return action();});
    this.tail=result.catch(error=>this.fail(error)).finally(()=>{--this.pendingCallbacks;++this.completedCallbacks;});
    return result;
  }
  call(name,returnType,types,args) {return this.module.ccall(name,returnType,types,args,{async:true});}
  bindCore(raw) {
    if(this.boundCores.has(raw))return raw;
    const core=Object.assign(Object.create(null),raw);
    for(const name of queuedVoid)if(typeof raw[name]==='function')core[name]=(...args)=>{
      void this.run(()=>raw[name](...args)).catch(()=>{});
    };
    this.boundCores.add(core);return core;
  }
  schedule(callback,data,delay) {
    const deliver=()=>{void this.run(()=>this.call('th14_async_invoke',null,['number','number'],[callback,data])).catch(()=>{});};
    if(delay<0){
      if(!this.requestFrame)throw new Error('requestAnimationFrame unavailable');
      this.requestFrame(deliver);
    }else this.setTimer(deliver,delay);
  }
  startFrames(callback,data) {
    if(!this.requestFrame)throw new Error('requestAnimationFrame unavailable');
    const tick=time=>{
      void this.run(()=>this.call('th14_async_frame','number',['number','number','number'],[callback,time,data]))
        .then(again=>{if(again&&!this.failure)this.requestFrame(tick);},()=>{});
    };
    return this.requestFrame(tick);
  }
}
