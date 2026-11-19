import {ApplicationNaturalClearCpuSession} from './ApplicationNaturalClearCpuSession.mjs';
const encode64=b=>{let s='';for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s);};
const decode64=s=>Uint8Array.from(atob(s),v=>v.charCodeAt(0));
const hex=s=>Uint8Array.from(s.match(/../g)||[],v=>parseInt(v,16));
export class PlayNaturalClearCpuSession extends ApplicationNaturalClearCpuSession {
 constructor(canvas){super(canvas);this.keys=new Set();this.glyphs=0;this.blobs=new Map();const dispatch=this.device.dispatch.bind(this.device);this.device.dispatch=(op,args,bytes)=>op===16&&!args.length?1:dispatch(op,args,bytes);}
 clearSurfaceRead(source,width,height,pointer,count){
  const d=this.device,gl=d.gl,token=source===d.backbufferToken?0:source,target=d.framebuffers.get(token);
  if(!target||target.width!==width||target.height!==height||count!==width*height*4)throw Error('Unrendered clear-preview target '+source.toString(16));
  const previous=gl.getParameter(gl.READ_FRAMEBUFFER_BINDING),rgba=new Uint8Array(count);
  try{gl.bindFramebuffer(gl.READ_FRAMEBUFFER,target.framebuffer);gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,rgba);if(gl.getError())throw Error('Clear-preview GPU readback failed');}finally{gl.bindFramebuffer(gl.READ_FRAMEBUFFER,previous);}
  // Native targets store their logical top row at GL row0 in this backend.
  for(let i=0;i<count;i+=4){const r=rgba[i];rgba[i]=rgba[i+2];rgba[i+2]=r;}
  this.bytes(pointer,count).set(rgba);this.clearReadbacks=(this.clearReadbacks||0)+1;return 1;
 }
 glyphsRequest(){const c=this.runtime,request={header:encode64(this.bytes(c.title_text_header(),108)),face:encode64(this.bytes(c.title_text_face(),c.title_text_face_bytes())),font:Array.from({length:13},(_,i)=>c.title_text_font_word(i)),input:encode64(this.bytes(c.title_text_bitmap(),c.title_text_bitmap_bytes())),draws:Array.from({length:c.title_text_command_count()},(_,i)=>({color:c.title_text_command_word(i,0)>>>0,x:c.title_text_command_word(i,1)|0,y:c.title_text_command_word(i,2)|0,n:c.title_text_command_word(i,3),text:encode64(this.bytes(c.title_text_command_data(i),c.title_text_command_word(i,3)))}))};
  const xhr=new XMLHttpRequest();xhr.open('POST','/glyphs',false);xhr.setRequestHeader('Content-Type','application/json');xhr.send(JSON.stringify(request));if(xhr.status!==200)throw Error('Glyph service failed: '+xhr.responseText);const reply=JSON.parse(xhr.responseText);if(!reply.created)throw Error('Font creation failed');const b=decode64(reply.bitmap);if(b.length!==c.title_text_bitmap_bytes())throw Error('Glyph bitmap size changed');this.bytes(c.title_text_bitmap(),b.length).set(b);++this.glyphs;return 1;
 }
 consumeBuffer(p,n){if(!n)return;const actual=this.runtime;this.runtime={...actual,common_composition_calls_data:()=>p,common_composition_calls_bytes:()=>n};try{super.consumeCalls();}finally{this.runtime=actual;}}
 async initialize(progress=()=>{}){
  this.build=await(await fetch('/build.json')).json();const raw=await(await fetch('/play.wasm')).arrayBuffer();if(await this.sha(raw)!==this.build.wasmSha256)throw Error('WebAssembly fingerprint changed');const {instance}=await WebAssembly.instantiate(raw,{wasi_snapshot_preview1:{fd_close:()=>8,fd_seek:()=>8,fd_write:()=>8},th143:{title_glyphs:()=>this.glyphsRequest(),title_text_upload:()=>1,title_clear_surface_read:(...args)=>this.clearSurfaceRead(...args)}});this.runtime=instance.exports;this.runtime._initialize();const c=this.runtime;
  for(let i=0;i<this.build.blobs.length;i+=6){await Promise.all(this.build.blobs.slice(i,i+6).map(async item=>{const b=new Uint8Array(await(await fetch('/blobs/'+item.sha256+'.bin')).arrayBuffer());if(b.length!==item.bytes||await this.sha(b)!==item.sha256)throw Error('Bootstrap input fingerprint changed');this.blobs.set(item.sha256,b);}));progress('读取资源 '+Math.min(i+6,this.build.blobs.length)+'/'+this.build.blobs.length);}
  let booted=false;for(const[i,action]of this.build.plan.entries()){
   c.boot_clear_device();const allocated=[];const args=action.args.map(arg=>{if(!arg?.blob)return arg;const b=this.blobs.get(arg.blob),p=c.allocate(b.length);this.bytes(p,b.length).set(b);allocated.push(p);return p;});
   let result;try{result=c[action.method](...args);}finally{for(const p of allocated.reverse())c.release(p);}if('expectedReturn'in action&&result!==action.expectedReturn)throw Error(action.method+' returned '+result+' instead of '+action.expectedReturn);
   if(action.method==='title_graphics_initialize'){booted=true;this.mirrorBackbuffer();this.consumeBuffer(c.boot_graphics_calls_data(),c.boot_graphics_calls_bytes());this.consumeBuffer(c.boot_mesh_calls_data(),c.boot_mesh_calls_bytes());}
   if(booted){this.mirrorBackbuffer();this.mirrorImages();this.consumeCalls();if(action.method.endsWith('_frame')||action.method==='common_composition_run')this.device.present();}
   if(i%8===0){progress('启动与菜单 '+(i+1)+'/'+this.build.plan.length);await new Promise(requestAnimationFrame);}
  }
  this.blobs.clear();this.keyBuffer=c.allocate(256);this.frames=0;
 }
 step(){const c=this.runtime,scripted=this.build.physicalInputs[this.frames];let input;
  if(scripted)input={...scripted,bytes:hex(scripted.keys)};else{const bytes=new Uint8Array(256),map={ArrowUp:0x26,ArrowDown:0x28,ArrowLeft:0x25,ArrowRight:0x27,KeyZ:0x5a,KeyX:0x58,Escape:0x1b,ShiftLeft:0x10,ShiftRight:0x10,ControlLeft:0x11,Enter:0x0d};for(const key of this.keys)if(key in map)bytes[map[key]]=0x80;input={bytes,enabled:1,config:0,keyboard:1,acquire:0,joystick:1};}
  this.bytes(this.keyBuffer,256).set(input.bytes);const result=c.title_long_frame(this.keyBuffer,input.enabled,input.config,input.keyboard,input.acquire,input.joystick);if(result<0)throw Error('Gameplay callback failed '+result+' at '+(c.title_gameplay_failed_entry()>>>0).toString(16)+' frame '+this.frames+' opcode '+c.title_gameplay_failed_opcode()+' completionStage '+c.title_natural_clear_stage()+' readbacks '+(this.clearReadbacks||0)+' writes '+c.title_clear_preview_file_writes());this.mirrorBackbuffer();this.mirrorImages();this.consumeCalls();this.device.present();return this.frames++;
 }
 async cpuSnapshot(frame){const c=this.runtime,region=(p,n)=>this.bytes(c.game_boot_region(p,n),n).slice();return{frame,poolSha256:await this.sha(region(0x72000000,0xff75ac)),applicationSha256:await this.sha(region(0x4e47d0,0xa34)),playerSha256:await this.sha(region(0x6a000000,0x184cc)),deviceCallsSha256:await this.sha(this.bytes(c.common_composition_calls_data(),c.common_composition_calls_bytes()).slice()),physicalDeviceSha256:await this.sha(this.bytes(c.title_device_data(),0x248).slice())};}
}
