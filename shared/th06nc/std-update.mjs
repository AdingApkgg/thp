const F=Math.fround;
// Background task 77bb0..78261. Fog calls are explicit renderer services;
// direction is the three floats published at native 4ff26c..274.
export function advanceStd(state,{paused=false,setFogColor=null,setFogRange=null}={}){
 const {v,program}=state,i=p=>v.getInt32(p,true),si=(p,x)=>v.setInt32(p,x,true),f=p=>v.getFloat32(p,true),sf=(p,x)=>v.setFloat32(p,F(x),true),copy=(to,from,n)=>state.owner.copyWithin(to,from,from+n),color=()=>setFogColor?.([v.getUint8(0x42),v.getUint8(0x41),v.getUint8(0x40)]),range=()=>setFogRange?.([f(0x44),f(0x48)]),lerp=(a,b,t)=>F(F(F(b-a)*t)+a);
 if(!v.getBigUint64(0xa8,true))return 1;
 if(paused){v.setUint32(0x1bc,0x60803030,true);return 1;}
 // Include the original sentinel so terminal position keys remain observable.
 const raw=new DataView(program.bytes.buffer,program.bytes.byteOffset,program.bytes.byteLength),record=index=>{const p=program.scriptOffset+index*20;if(p<program.scriptOffset||p+20>program.bytes.length)throw Error('TH06nc STD: camera cursor outside program');return {time:raw.getInt32(p,true),op:raw.getInt16(p+4,true),p};};
 let current=record(i(0x24)),commands=0;
 while(current.op>=0&&current.op<=5){
  if(++commands>10000)throw Error('TH06nc STD: camera dispatch limit');const {time,op,p}=current;
  if(op===0){
   if(time!==-1&&i(0xb4)<time)break;
   state.owner.set(program.bytes.subarray(p+8,p+20),0x1f8);copy(0xc0,0x1f8,12);
   if(time===-1)break;
   si(0x204,time);si(0x24,i(0x24)+1);let next=i(0x24);do{current=record(next++);}while(current.op!==0);si(0x3c,current.time);state.owner.set(program.bytes.subarray(current.p+8,current.p+20),0x30);break;
  }
  if(op!==5&&i(0xb4)<time)break;
  if(op===1){state.owner.set(program.bytes.subarray(p+8,p+20),0x40);if(!i(0x90)){color();range();}copy(0x58,0x40,12);si(0x24,i(0x24)+1);}
  else if(op===2){copy(4,0x10,12);state.owner.set(program.bytes.subarray(p+8,p+20),0x10);si(0x24,i(0x24)+1);}
  else if(op===3){const duration=raw.getInt32(p+8,true);if(duration===-1){copy(0x208,0xb0,8);si(0x210,i(0x24)+1);copy(0x214,0xc0,12);si(0x24,i(0x24)+1);}else if(duration===-2){copy(0xb0,0x208,8);copy(0xc0,0x214,12);si(0x24,i(0x210));}else{si(0x78,duration);si(0x80,0);si(0x7c,-999);si(0x24,i(0x24)+1);}}
  else if(op===4){copy(0x4c,0x40,12);si(0x90,raw.getInt32(p+8,true));si(0x98,0);si(0x94,-999);si(0x24,i(0x24)+1);}
  else if(op===5){if(!v.getUint8(0x68))break;v.setUint8(0x68,0);si(0x24,i(0x24)+1);}
  current=record(i(0x24));
 }
 if(current.time!==-1){const t=F(F(F(i(0xb4))-F(i(0x204)))/F((i(0x3c)-i(0x204))|0));for(let k=0;k<3;k++)sf(0xc0+k*4,lerp(f(0x1f8+k*4),f(0x30+k*4),t));}
 if(i(0x78)!==0){const duration=i(0x78),frame=i(0x80),next=frame<duration?(frame+1)|0:duration;si(0x7c,frame<duration?frame:-999);si(0x80,next);const t=F(F(next)/F(duration));state.direction=Array.from({length:3},(_,k)=>lerp(f(4+k*4),f(0x10+k*4),t));}
 if(i(0x90)!==0){si(0x94,i(0x98));si(0x98,i(0x98)+1);const ratio=F(F(i(0x98))/F(i(0x90))),t=Number.isNaN(ratio)?ratio:Math.min(1,ratio);for(let k=0;k<4;k++)v.setUint8(0x40+k,Math.trunc(lerp(v.getUint8(0x4c+k),v.getUint8(0x58+k),t)));for(let k=0;k<2;k++)sf(0x44+k*4,lerp(f(0x50+k*4),f(0x5c+k*4),t));color();range();if(i(0x98)>=i(0x90))si(0x90,0);}
 if(current.op!==5){si(0xb0,i(0xb4));si(0xb4,i(0xb4)+1);}
 const file=new DataView(state.bytes.buffer,state.bytes.byteOffset,state.bytes.byteLength);
 for(const object of program.objects){if(!(file.getUint8(object.offset+3)&1))continue;let live=0;for(const face of object.primitives){const vm=state.vms[file.getInt16(face.offset+6,true)];if(face.type===0||face.type===1)vm.tick();if(vm.pointer(0xf8))live++;}if(!live)file.setUint8(object.offset+3,file.getUint8(object.offset+3)&254);}
 if(i(0xb8)>=1){if(i(0)===60)si(0xb8,i(0xb8)+1);si(0,i(0)+1);state.overlayVm.tick();}
 return 1;
}
