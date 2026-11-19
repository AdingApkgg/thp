const F=Math.fround;
// Item movement 42aef..42cb7. The owner handles pickup, animation and clock.
export function advanceItemMotion(item,{playerPosition=[0,0,0],playerState=0,atan2=Math.atan2,sin=Math.sin,cos=Math.cos}={}){
 const {v}=item,f=p=>v.getFloat32(p,true),sf=(p,x)=>v.setFloat32(p,F(x),true),valid=playerState===0||playerState===3;let mode=v.getUint8(0xc);
 if(!valid&&mode===1){mode=0;v.setUint8(0xc,0);v.setBigUint64(0x1c,0n,true);v.setInt32(0x24,0,true);}
 if(valid&&(mode===1||F(128)>F(playerPosition[1]))){
  const dx=F(F(playerPosition[0])-f(0x10)),dy=F(F(playerPosition[1])-f(0x14)),angle=dx===0&&dy===0?F(Math.PI/2):F(atan2(dy,dx));sf(0x1c,F(cos(angle))*F(8));sf(0x20,F(sin(angle))*F(8));v.setUint8(0xc,1);
 }else if(mode===2){
  const clock=v.getInt32(8,true);if(clock<60){const t=F(F(clock)/F(60)),remaining=F(F(1)-t);sf(0x10,F(F(remaining*f(0x1c))+F(t*f(0x28))));sf(0x14,F(F(t*f(0x2c))+F(remaining*f(0x20))));sf(0x18,F(F(t*f(0x30))+F(remaining*f(0x24))));return true;}
  if(clock===60){v.setBigUint64(0x1c,0n,true);v.setInt32(0x24,0,true);}
 }else if(mode===0){v.setInt32(0x1c,0,true);v.setInt32(0x24,0,true);if(F(-2.2)>f(0x20))sf(0x20,-2.2);}
 for(let k=0;k<3;k++)sf(0x10+k*4,F(f(0x10+k*4)+f(0x1c+k*4)));
 if(f(0x14)>=F(464)){v.setUint8(0,0);return false;}
 if(F(3)>f(0x20))sf(0x20,F(f(0x20)+F(0.03)));else sf(0x20,3);return true;
}
