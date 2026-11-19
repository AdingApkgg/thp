const F=Math.fround;
// Original owner 11c2a..11f2d: four size/script passes, all using 2D draw.
export function drawBullets(pool,draw,{worldOffset=[0,0]}={}){
 for(let pass=0;pass<4;pass++)for(let slot=0;slot<640;slot++){
  const entry=pool.entry(slot),{v}=entry,state=v.getUint16(0x44,true);if(!state)continue;
  const size=v.getUint8(0x5f0),script=v.getUint16(0x88,true),special=script===513||script===515;
  if(!(pass===0?size>16:pass===1?size===16&&special:pass===2?size===16&&!special:size===8))continue;
  const index=state>=2&&state<=5?state-1:0,vm=entry.anms[index];if(!vm)throw Error('TH06nc: missing bullet draw ANM');
  const a=vm.v;a.setUint32(0xc8,v.getUint32(0x30,true),true);a.setUint32(0xcc,v.getUint32(0x34,true),true);a.setInt32(0xd0,0,true);a.setUint32(0xec,a.getUint32(0xec,true)|0xffffff,true);
  if(a.getUint16(0x88,true)!==0)a.setFloat32(0xa4,F(F(Math.PI/2)-v.getFloat32(0x40,true)),true);
  const x=a.getFloat32(0xc8,true),y=a.getFloat32(0xcc,true);a.setFloat32(0xc8,F(x+F(worldOffset[0])),true);a.setFloat32(0xcc,F(y+F(worldOffset[1])),true);
  try{draw(vm,{snap:false,slot,part:'bullet',space:'screen'});}finally{a.setFloat32(0xc8,x,true);a.setFloat32(0xcc,y,true);}
 }
}
