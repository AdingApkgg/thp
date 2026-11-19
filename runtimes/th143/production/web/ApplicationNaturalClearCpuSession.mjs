import {SessionDevice} from './SessionDeviceDirectClip.mjs';
const ONE=0x3f800000,RATES=[ONE,0x3f000000,0,0x3fa00000];
export class ApplicationNaturalClearCpuSession {
 constructor(canvas){this.device=new SessionDevice(canvas);this.canvas=canvas;this.runtime=null;this.imageCursor=0;this.backbufferCursor=0;this.frames=0;this.commands=0;this.mesh=null;this.stream=null;}
 bytes(p,n){return new Uint8Array(this.runtime.memory.buffer,p,n);}
 transfer(b,fn){const p=this.runtime.allocate(b.length);this.bytes(p,b.length).set(b);try{return fn(p,b.length);}finally{this.runtime.release(p);}}
 async initialize(){
  this.build=await(await fetch('/build.json')).json();const raw=await(await fetch('/application.wasm')).arrayBuffer();if(await this.sha(raw)!==this.build.wasmSha256)throw Error('WebAssembly fingerprint changed');
  const wasi={fd_close:()=>8,fd_seek:()=>8,fd_write:()=>8};const {instance}=await WebAssembly.instantiate(raw,{wasi_snapshot_preview1:wasi});this.runtime=instance.exports;this.runtime._initialize();
  const encode=new TextEncoder();for(const[n,h]of Object.entries(this.build.files)){const response=await fetch('/resources/'+encodeURIComponent(n));if(!response.ok)throw Error(n+' unavailable');const b=new Uint8Array(await response.arrayBuffer());if(await this.sha(b)!==h)throw Error(n+' fingerprint changed');this.transfer(encode.encode(n),(np,nn)=>this.transfer(b,(p,bytes)=>this.runtime.add_file(np,nn,p,bytes)));}
  for(const[i,hex]of this.build.fontFamilyNames.entries())this.transfer(Uint8Array.from(hex.match(/../g),v=>parseInt(v,16)),(p,n)=>this.runtime.boot_family_name(i,p,n));
  const c=this.runtime;if(!c.boot_common_initialize(0,640,480,ONE,0)||!c.boot_graphics())throw Error('Application preparation failed');this.consumeCalls();c.boot_clear_device();if(!c.boot_common_finish_initialization())throw Error('Original application startup failed');this.mirrorBackbuffer();this.consumeCalls();
  c.boot_clear_device();if(!c.common_load_run())throw Error('Common loader failed at '+(c.common_load_failed_entry()>>>0).toString(16));this.mirrorImages();
  let pumps=0;while(Array.from({length:30},(_,i)=>c.common_load_pending(i)).some(Boolean)){if(++pumps>128||!c.common_load_pump())throw Error('Resource pump failed');this.mirrorImages();await new Promise(requestAnimationFrame);}
  for(const op of [0,0,2,1,2,3,1]){if(!c.common_composition_targets_run(op))throw Error('Target lifecycle failed');this.mirrorBackbuffer();this.mirrorImages();}
  c.common_pool_frame_prepare();for(let i=0;i<180;i++){if(c.boot_common_frame(RATES[i%4])!==5)throw Error('Common update failed');this.consumeCalls();if(i%30===0)await new Promise(requestAnimationFrame);}
  for(let cycle=0;cycle<3;cycle++)for(const op of [0,0x445e20,0x445d10,0x445fc0,0x445ec0,0x446110,0x446060,0x446240,0x4461e0,1]){if(!c.common_composition_run(op))throw Error('Application composition failed');this.consumeCalls();}
  if(!c.boot_render_probe())throw Error('Animation layer creation failed');this.pumps=pumps;
 }
 mirrorBackbuffer(){const c=this.runtime,events=new Uint32Array(c.memory.buffer,c.common_backbuffer_events_data(),c.common_backbuffer_events_words());while(this.backbufferCursor<events.length){const i=this.backbufferCursor;this.device.dispatch(events[i]===0?20:21,[events[i+1]],new Uint8Array());this.backbufferCursor+=3;}}
 mirrorImages(){
  const c=this.runtime,events=new Uint32Array(c.memory.buffer,c.common_image_events_data(),c.common_image_events_words()),changed=new Set();while(this.imageCursor<events.length){const i=this.imageCursor,kind=events[i],token=events[i+1];if(kind===0||kind===2)changed.add(token);else if(kind===3){if(this.device.textures.has(token))this.device.dispatch(17,[token],new Uint8Array());changed.delete(token);}this.imageCursor+=3;}
  for(let i=0;i<c.common_image_count();i++){const token=c.common_image_token(i)>>>0;if(changed.has(token))this.device.dispatch(16,[token,c.common_image_format(i),c.common_image_width(i),c.common_image_height(i)],this.bytes(c.common_image_data(i),c.common_image_bytes(i)));}
 }
 consumeCalls(){
  const c=this.runtime,bytes=this.bytes(c.common_composition_calls_data(),c.common_composition_calls_bytes()),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);let at=0;
  while(at<bytes.length){if(at+12>bytes.length)throw Error('Truncated device header');const op=v.getUint32(at,true),argsBytes=v.getUint32(at+4,true),n=v.getUint32(at+8,true);at+=12;if(argsBytes%4||at+argsBytes+n>bytes.length)throw Error('Invalid device payload');const args=Array.from({length:argsBytes/4},(_,i)=>v.getUint32(at+i*4,true));at+=argsBytes;const raw=bytes.subarray(at,at+n);at+=n;
   if(op===11){if(args[0]!==720)throw Error('Unknown static mesh size');this.mesh={token:0x6e037000,data:null};}
   else if(op===12){if(!this.mesh||args[0]!==this.mesh.token)throw Error('Unknown static mesh lock');}
   else if(op===13){if(!this.mesh||args[0]!==this.mesh.token)throw Error('Unknown static mesh unlock');this.mesh.data=this.bytes(c.boot_region(0x6e038000,720),720).slice();}
   else if(op===8){if(args[0]!==0||!this.mesh||args[1]!==this.mesh.token)throw Error('Unknown stream');this.stream={offset:args[2],stride:args[3]};}
   else if(op===9){if(!this.stream||!this.mesh?.data)throw Error('Unbound mesh');const [kind,start,count]=args,stride=this.stream.stride,vertices=kind===4?count*3:kind>=5?count+2:0;if(!vertices)throw Error('Unsupported mesh primitive');const offset=this.stream.offset+start*stride;this.device.dispatch(5,[kind,count,stride],this.mesh.data.subarray(offset,offset+vertices*stride));}
   else this.device.dispatch(op,args,raw);++this.commands;
  }
 }
 step(){const c=this.runtime,rate=this.frames<60?RATES[this.frames%4]:ONE;if(c.boot_render_frame(rate)!==54)throw Error('Registered frame failed at '+(c.boot_render_failed()>>>0).toString(16));this.mirrorImages();this.mirrorBackbuffer();this.consumeCalls();this.device.present();return this.frames++;}
 async sha(b){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b)),n=>n.toString(16).padStart(2,'0')).join('');}
 async cpuSnapshot(frame){const c=this.runtime,region=(p,n)=>this.bytes(c.boot_region(p,n),n).slice();return{frame,poolSha256:await this.sha(region(0x72000000,0xff75ac)),applicationSha256:await this.sha(region(0x4e47d0,0xa34)),asciiSha256:await this.sha(region(0x71000000,0x191f8)),rng:Array.from(this.bytes(c.common_load_rng_data(),16),v=>v.toString(16).padStart(2,'0')).join(''),deviceCallsSha256:await this.sha(this.bytes(c.common_composition_calls_data(),c.common_composition_calls_bytes()).slice())};}
}
