import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI);
const normalize=value=>{let a=F(value+0),n=0;while(a>PI){a=F(a-TAU);if(n++>16)break;}while(-PI>a){a=F(a+TAU);if(n++>16)break;}return a;};
// Active-state motion 10ab5..11060. Caller handles appearance/cancel states,
// culling, player contact, main ANM and the final bullet clock increment.
export function advanceBulletMotion(entry,{sin=Math.sin,cos=Math.cos,atan2=Math.atan2,playerPosition=[0,0,0]}={}){
 const v=entry.v,f=p=>v.getFloat32(p,true),i=p=>v.getInt32(p,true),sf=(p,x)=>v.setFloat32(p,F(x),true),si=(p,x)=>v.setInt32(p,x,true);let flags=v.getUint16(0x14,true);const clock=i(0x2c);
 const clear=mask=>{flags&=~mask;v.setUint16(0x14,flags,true);};
 const velocity=(angle,speed)=>{sf(8,F(cos(angle))*speed);sf(0xc,F(sin(angle))*speed);};
 if(flags&1){if(clock<=16){const speed=F(F(F(5)-F(F(F(clock)*F(5))*F(1/16)))+f(0x24));velocity(f(0x40),speed);}else clear(1);}
 else if(flags&0x10){if(clock>=i(0x48))clear(0x10);else{for(const [p,a]of [[8,0x608],[0xc,0x60c],[0x10,0x610]])sf(p,F(f(a)+f(p)));sf(0x40,atan2(f(0xc),f(8)));}}
 else if(flags&0x20){if(clock>=i(0x48))clear(0x20);else{const angle=normalize(F(f(0x18)+f(0x40))),speed=F(f(0x600)+f(0x24));sf(0x40,angle);sf(0x24,speed);velocity(angle,speed);}}
 const turnMask=flags&0x40?0x40:flags&0x100?0x100:flags&0x80?0x80:0;
 if(turnMask){
  const count=i(0x1c),period=i(4);let speed;
  if(clock>=Math.imul(count+1,period)){
   si(0x1c,count+1);if(i(0x1c)>=i(0x20))clear(turnMask);
   let angle;if(turnMask===0x40)angle=F(f(0x614)+f(0x40));else if(turnMask===0x100)angle=f(0x614);else{const dx=F(F(playerPosition[0])-f(0x30)),dy=F(F(playerPosition[1])-f(0x34));angle=F((dx===0&&dy===0?F(Math.PI/2):F(atan2(dy,dx)))+f(0x614));}
   speed=f(0);sf(0x24,speed);sf(0x40,angle);
  }else{speed=f(0x24);const elapsed=F(F(clock)-F(Math.imul(count,period)));speed=F(speed-F(F(elapsed*speed)/F(period)));}
  velocity(f(0x40),speed);
 }else if(flags&0xc00){
  const mask=flags&0x400?0x400:0x800,[height,width]=spriteLogicalSize(entry.anms[0].boundSprite),halfX=F(width*F(0.5)),halfY=F(height*F(0.5)),x=f(0x30),y=f(0x34);
  if(F(x+halfX)<0||F(x-halfX)>384||F(y+halfY)<0||F(y-halfY)>448){
   let angle=f(0x40);if(x<0||x>=384)angle=normalize(F(-angle-PI));if(y<0||(mask===0x400&&y>=448))angle=F(-angle);
   sf(0x40,angle);const speed=f(0);sf(0x24,speed);velocity(angle,speed);si(0x1c,i(0x1c)+1);if(i(0x1c)>=i(0x20))clear(mask);
  }
 }
 for(const [p,a]of [[0x30,8],[0x34,0xc],[0x38,0x10]])sf(p,F(f(p)+f(a)));
}
