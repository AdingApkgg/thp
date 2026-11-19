const F=Math.fround;
// Owner draw 11b0a..11c2a: above-screen item arrows and normal sprites.
export function drawItems(pool,draw,{worldOffset=[0,0]}={}){
 for(let slot=0;slot<1024;slot++){
  if(!pool.storage[slot*0x160])continue;const item=pool.entry(slot),{v,vm}=item;if(!vm)throw Error('TH06nc: item draw ANM missing');const a=vm.v,y=v.getFloat32(0x14,true),normal=v.getUint8(0x158)!==0;
  a.setUint32(0xc8,v.getUint32(0x10,true),true);a.setFloat32(0xcc,y,true);a.setFloat32(0xd0,F(.01),true);
  if(F(-8)>y){
   a.setFloat32(0xcc,8,true);if(normal){vm.bindSprite(0x207+v.getInt8(0x34));v.setUint8(0x158,0);}
   const fade=F(F(F(F(8)-y)*F(255))*F(1/128)),alpha=Math.max(64,255-Math.trunc(fade));a.setUint32(0xec,(a.getUint32(0xec,true)&0xffffff)|(alpha<<24),true);
  }else if(!normal){vm.bindSprite(0x200+v.getInt8(0x34));v.setUint8(0x158,1);a.setUint32(0xec,0xffffffff,true);}
  const x=a.getFloat32(0xc8,true),yy=a.getFloat32(0xcc,true);a.setFloat32(0xc8,F(x+F(worldOffset[0])),true);a.setFloat32(0xcc,F(yy+F(worldOffset[1])),true);
  try{draw(vm,{snap:true,space:'screen',part:'item',slot});}finally{a.setFloat32(0xc8,x,true);a.setFloat32(0xcc,yy,true);}
 }
}
