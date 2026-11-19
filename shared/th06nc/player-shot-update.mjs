import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround,sqrt=x=>F(Math.sqrt(x));
// Owner shot/cooldown block 69740..69b09. Main player ANM ticks before this.
export function advancePlayerShots(player){
 const {bytes,v,anms}=player;
 for(const p of [0x79ec,0x79f4]){const n=v.getInt32(p,true);if(n)v.setInt32(p,n-1,true);}
 for(let slot=0;slot<80;slot++){
  const base=0x410+slot*0x170,d=new DataView(bytes.buffer,bytes.byteOffset+base,0x170),state=d.getUint16(0x10,true);if(!state)continue;
  const f=p=>d.getFloat32(p,true),sf=(p,x)=>d.setFloat32(p,F(x),true),kind=d.getInt16(0x12,true),vm=anms.get(base+0x18);if(!vm)throw Error('TH06nc: active player shot ANM missing');
  if(kind===3){
   const channel=d.getInt16(0x138,true),clock=v.getInt32(0x79ec+channel*8,true);if(clock===70||clock===1)vm.interrupt(1);
   const source=0x7874+d.getInt16(0x14c,true)*12;for(let k=0;k<3;k++)d.setUint32(0x13c+k*4,v.getUint32(source+k*4,true),true);
   sf(0x13c,F(f(0x148)+f(0x13c)));sf(0x140,F(f(0x140)*F(0.5)));sf(0x144,0.44);const height=F(f(0x140)+f(0x140));sf(0x164,height);sf(0xfc,F(height/F(14)));
  }else if(kind===2&&state===1)sf(0xc,F(f(0xc)-F(0.3)));
  else if(kind===1&&state===1){
   const targetX=v.getFloat32(0x7740,true),targetY=v.getFloat32(0x7744,true),clock=d.getInt32(4,true);
   if(targetX>F(-100)&&clock<40&&clock!==d.getInt32(0,true)){
    const dx=F(targetX-f(0x13c)),dy=F(targetY-f(0x140)),distance=sqrt(F(F(dy*dy)+F(dx*dx))),denominator=Math.max(F(1),F(distance/F(f(0x154)*F(0.25))));
    const x=F(F(dx/denominator)+f(8)),y=F(F(dy/denominator)+f(0xc)),norm=sqrt(F(F(y*y)+F(x*x)));let speed=Math.min(F(10),norm);sf(0x154,speed);if(F(1)>speed){sf(0x154,1);speed=F(1);}sf(0xc,F(F(speed*y)/norm));sf(8,F(F(speed*x)/norm));
   }else if(F(10)>f(0x154)){
    const x=f(8),y=f(0xc),speed=F(f(0x154)+F(1/3)),norm=sqrt(F(F(x*x)+F(y*y)));sf(0x154,speed);sf(8,F(F(x*speed)/norm));sf(0xc,F(F(y*speed)/norm));
   }
  }
  d.setUint32(0xe8,d.getUint32(0x144,true),true);const x=F(f(8)+f(0x13c)),y=F(f(0xc)+f(0x140));sf(0x13c,x);sf(0xe0,x);sf(0x140,y);sf(0xe4,y);
  if(kind!==3){const [height,width]=spriteLogicalSize(vm.boundSprite),hx=F(width*F(0.5)),hy=F(height*F(0.5));if(F(x+hx)<0||F(x-hx)>384||F(y+hy)<0||F(y-hy)>448)d.setUint16(0x10,0,true);}
  if(vm.tick())d.setUint16(0x10,0,true);const clock=d.getInt32(4,true);d.setInt32(0,clock,true);d.setInt32(4,clock+1,true);
 }
}
