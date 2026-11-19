import {PlayNaturalClearCpuSession} from './PlayNaturalClearCpuSession.mjs';
const hex=s=>Uint8Array.from(s.match(/../g)||[],v=>parseInt(v,16));
// Keep the already observed120-frame browser implementation frozen. The new
// module includes actual Root cleanup and cooperatively resumes its worker
// when the application has created the next Root, independent of frame index.
export class CompleteNaturalClearCpuSession extends PlayNaturalClearCpuSession {
 async initialize(progress=()=>{}){
  this.build=await(await fetch('/build.json')).json();const raw=await(await fetch('/play.wasm')).arrayBuffer();if(await this.sha(raw)!==this.build.wasmSha256)throw Error('WebAssembly fingerprint changed');const {instance}=await WebAssembly.instantiate(raw,{wasi_snapshot_preview1:{fd_close:()=>8,fd_seek:()=>8,fd_write:()=>8},th143:{title_glyphs:()=>this.glyphsRequest(),title_text_upload:()=>1,title_clear_surface_read:(...args)=>this.clearSurfaceRead(...args)}});this.runtime=instance.exports;this.runtime._initialize();const c=this.runtime;
  for(let i=0;i<this.build.blobs.length;i+=6){await Promise.all(this.build.blobs.slice(i,i+6).map(async item=>{const b=new Uint8Array(await(await fetch('/blobs/'+item.sha256+'.bin')).arrayBuffer());if(b.length!==item.bytes||await this.sha(b)!==item.sha256)throw Error('Bootstrap input fingerprint changed');this.blobs.set(item.sha256,b);}));progress('读取资源 '+Math.min(i+6,this.build.blobs.length)+'/'+this.build.blobs.length);}
  let booted=false;for(const[i,action]of this.build.plan.entries()){
   c.boot_clear_device();const allocated=[];const args=action.args.map(arg=>{if(!arg?.blob)return arg;const b=this.blobs.get(arg.blob),p=c.allocate(b.length);this.bytes(p,b.length).set(b);allocated.push(p);return p;});
   let result;try{result=c[action.method](...args);}finally{for(const p of allocated.reverse())c.release(p);}if('expectedReturn'in action&&result!==action.expectedReturn)throw Error(action.method+' returned '+result+' instead of '+action.expectedReturn);
   if(action.method==='title_graphics_initialize'){booted=true;this.mirrorBackbuffer();this.consumeBuffer(c.boot_graphics_calls_data(),c.boot_graphics_calls_bytes());this.consumeBuffer(c.boot_mesh_calls_data(),c.boot_mesh_calls_bytes());}
   if(booted){this.mirrorBackbuffer();this.mirrorImages();this.consumeCalls();if(action.method.endsWith('_frame')||action.method==='common_composition_run')this.device.present();}
   if(i%8===0){progress('启动与菜单 '+(i+1)+'/'+this.build.plan.length);await new Promise(resolve=>{const channel=new MessageChannel();channel.port1.onmessage=()=>{channel.port1.close();channel.port2.close();resolve();};channel.port2.postMessage(0);});}
  }
  this.blobs.clear();this.keyBuffer=c.allocate(256);this.frames=0;if(typeof c.title_retry_reload_frame!=='function')throw Error('Reload runtime missing');this.runtime={...c,title_long_frame:c.title_retry_reload_frame};
 }
 async cpuSnapshot(frame){
  const result=await super.cpuSnapshot(frame),c=this.runtime,region=(p,n)=>this.bytes(c.game_boot_region(p,n),n).slice();
  for(const[key,p,n]of [['asciiSha256',0x71000000,0x191f8],['audioSha256',0x53b1e0,0x57b0],['schedulerSha256',0x6e008000,0x58],['stageSha256',0x6c010000,0x43a0],['menuSha256',0x6b020000,0x91c4],['enemySha256',0x6b003000,0xe8],['gameStateSha256',0x4e46f0,0xe0]])result[key]=await this.sha(region(p,n));
  result.rootSha256=await this.sha(this.bytes(c.title_root_data(),0x9c).slice());result.rng=Array.from(this.bytes(c.common_load_rng_data(),16),v=>v.toString(16).padStart(2,'0')).join('');result.images=[];
  for(let i=0;i<c.common_image_count();++i)result.images.push({token:c.common_image_token(i)>>>0,format:c.common_image_format(i),width:c.common_image_width(i),height:c.common_image_height(i),references:c.common_image_refs(i),bytes:c.common_image_bytes(i),sha256:await this.sha(this.bytes(c.common_image_data(i),c.common_image_bytes(i)).slice())});
  result.images.sort((a,b)=>a.token-b.token);return result;
 }
}
