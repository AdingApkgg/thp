const F=Math.fround;
// Laser portion of projectile draw manager, 119a7..11b0a.
export function drawLasers(pool,draw,{sin=Math.sin,cos=Math.cos,worldOffset=[0,0]}={}){
  const invoke=(vm,snap,slot,part)=>{const v=vm.v,x=v.getFloat32(0xc8,true),y=v.getFloat32(0xcc,true);v.setFloat32(0xc8,F(x+F(worldOffset[0])),true);v.setFloat32(0xcc,F(y+F(worldOffset[1])),true);try{draw(vm,{snap,slot,part,space:part==='beam'?'world':'screen'});}finally{v.setFloat32(0xc8,x,true);v.setFloat32(0xcc,y,true);}};
 for(let slot=0;slot<64;slot++){
  const laser=pool.entry(slot),{v,main,end}=laser;if(!v.getUint8(0x274))continue;if(!main||!end)throw Error('TH06nc: active laser draw bindings missing');
  const angle=v.getFloat32(0x260,true),s=F(sin(angle)),c=F(cos(angle)),tail=v.getFloat32(0x10,true),head=v.getFloat32(0x14,true),distance=F(F(F(head-tail)*F(0.5))+tail),x=v.getFloat32(0x278,true),y=v.getFloat32(0x27c,true);
  v.setInt32(0xf0,0,true);v.setUint16(0x284,65535,true);v.setFloat32(0xe8,F(F(distance*c)+x),true);v.setFloat32(0xec,F(F(distance*s)+y),true);invoke(main,false,slot,'beam');
  if(!(F(32)>tail||v.getFloat32(0x26c,true)===0))continue;
  v.setUint32(0x204,v.getUint32(0x204,true)|8,true);v.setUint32(0x22c,v.getUint32(0x10c,true)|0xff000000,true);v.setInt32(0x210,0,true);v.setFloat32(0x208,F(F(tail*c)+x),true);v.setFloat32(0x20c,F(F(tail*s)+y),true);
  const width=F(v.getFloat32(4,true)/F(10));let scale=F(F(F(F(32)-tail)*F(1/32))*width);if(0>scale)scale=width;v.setFloat32(0x224,scale,true);v.setFloat32(0x228,scale,true);invoke(end,true,slot,'origin');
 }
}
