const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI);
// One emission in native f870: 0 <= way < ways, 0 <= layer < layers.
// Caller allocates a free bullet before invoking this (pool exhaustion consumes
// no random numbers). Values are rounded in the original instruction order.
export function bulletPattern(descriptor,way,layer,{aim=0,rng=null}={}){
 const d=new DataView(descriptor.buffer,descriptor.byteOffset,descriptor.byteLength),ways=d.getInt16(0x18,true),layers=d.getInt16(0x1a,true),mode=d.getUint16(0x30,true),base=d.getFloat32(0x34,true),spread=d.getFloat32(0x38,true),fast=d.getFloat32(4,true),slow=d.getFloat32(8,true),delta=F(fast-slow);
 let speed=F(fast-F(F(F(layer)*delta)/F(layers))),angle=0;
 const random=()=>{if(!rng)throw Error('TH06nc: random bullet pattern requires RNG');return rng.float01();};
 switch(mode){
  case 0:case 1:{
   const factor=ways&1?Math.trunc((way+1)/2):Math.trunc(way/2);angle=F(F(factor)*spread);
   if(!(ways&1))angle=F(angle+F(spread*F(0.5)));
   angle=F(angle+0);if(way&1)angle=F(angle*F(-1));if(mode===0)angle=F(angle+F(aim));angle=F(angle+base);break;
  }
  case 2:case 3:{
   const ring=F(F(F(way)*TAU)/F(ways)),start=F(F(F(layer)*spread)+base);
   angle=F(start+F(ring+F((mode===2?F(aim):0)+0)));break;
  }
  case 4:case 5:{
   const ring=F(F(F(way)*TAU)/F(ways)),half=F(PI/F(ways));
   angle=F(F(ring+F(half+F((mode===4?F(aim):0)+0)))+base);break;
  }
  case 6:angle=F(F(random()*F(base-spread))+spread);break;
  case 7:{
   const r=random(),ring=F(F(F(way)*TAU)/F(ways));
   angle=F(F(F(F(layer)*spread)+base)+F(ring+0));speed=F(F(r*delta)+slow);break;
  }
  case 8:angle=F(F(random()*F(base-spread))+spread);speed=F(F(random()*F(fast-slow))+slow);break;
 }
 const rawAngle=angle;angle=F(angle+0);let wraps=0;
 while(angle>PI){angle=F(angle+F(-TAU));if(wraps++>16)break;}
 while(-PI>angle){angle=F(angle+TAU);if(wraps++>16)break;}
 return {angle,speed,rawAngle};
}
