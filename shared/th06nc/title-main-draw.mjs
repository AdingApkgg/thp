// Stable state-3 menu draw loop 0x140054f96..0x1400551ef, no menu slide effect.
// Background and title00 overlay are drawn by their separate owner branches.
const F=Math.fround;
export function drawStableTitleMain(group,draw,{disabled=new Uint8Array(173),hasTexture=()=>true,state=3,selection=0,pulse=0}={}){
 for(let index=0;index<149;index++){
  const vm=group.slots.get(0x9640+index*288);
  if(disabled[index]||!vm||!vm.pointer(0x100)||vm.boundBinding?.active===false||!hasTexture(vm.boundResource??vm.resource))continue;
  const v=vm.v,saved=vm.state.slice(0xc8,0xd4),color=v.getUint32(0xec,true);
  try{
   if(state===11&&index===126+selection*2){
    const t=pulse-Math.trunc(pulse/72)*72;
    const a=(t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30))&255;
    const gray=(208+Math.trunc((a-128)*47/127))&255;
    v.setUint32(0xec,(color&0xff000000)|(gray*0x10101),true);
   }
   for(let i=0;i<12;i+=4)v.setFloat32(0xc8+i,F(v.getFloat32(0xc8+i,true)+v.getFloat32(0x18+i,true)),true);
   if(index<9||index===50){v.setFloat32(0xc8,F(v.getFloat32(0xc8,true)-F(4.44444465637207)),true);v.setFloat32(0xcc,F(v.getFloat32(0xcc,true)-F(24.44444465637207)),true);}
   if(index>=51&&index<=69)v.setFloat32(0xcc,F(v.getFloat32(0xcc,true)-8),true);
   draw(vm,{snap:true});
  }finally{vm.state.set(saved,0xc8);v.setUint32(0xec,color,true);}
 }
}
