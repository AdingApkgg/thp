const F=Math.fround;
// Enemy ECL post-script movement phase 28840..28a7d. Position integration is external.
export function advanceEclMotion(enemy,{sin,cos,atan2}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),mode=v.getUint8(0xbc)&3,f=p=>v.getFloat32(p,true),put=(p,x)=>v.setFloat32(p,x,true);
 if(mode===2){
  const clock=(v.getInt32(0x260,true)-1)|0;v.setInt32(0x260,clock,true);
  let t=Math.min(1,F(F(clock)/F(v.getInt32(0x264,true))));
  const ease=(v.getUint8(0xbc)>>>2)&7;
  if(ease===0)t=F(1-t);
  else if(ease===1)t=F(1-F(t*t));
  else if(ease===2)t=F(1-F(F(F(t*t)*t)*t));
  else if(ease===3){t=F(1-t);t=F(t*t);}
  else if(ease===4){t=F(1-t);t=F(F(F(t*t)*t)*t);}
  for(let i=0;i<3;i++)put(0x1084+i*4,F(F(F(t*f(0x244+i*4))+f(0x250+i*4))-f(0xb0+i*4)));
  if(!atan2)throw Error('TH06nc ECL: movement requires atan2 service');put(0x22c,atan2(f(0x1088),f(0x1084)));
  if(clock<=0){
   v.setUint8(0xbc,v.getUint8(0xbc)&0xfc);for(let i=0;i<3;i++)put(0xb0+i*4,F(f(0x250+i*4)+f(0x244+i*4)));
   for(const p of [0x1084,0x1088,0x108c])put(p,0);
  }
 }else if(mode===1){
  if(!sin||!cos)throw Error('TH06nc ECL: polar movement requires shared sine/cosine services');
  let angle=F(f(0xc48)+f(0x22c)),count=0;
  while(angle>F(Math.PI)){angle=F(angle+F(-2*Math.PI));if(count++>16)break;}
  while(F(-Math.PI)>angle){angle=F(angle+F(2*Math.PI));if(count++>16)break;}
  put(0x22c,angle);const speed=F(f(0xf78)+f(0x3c));put(0x3c,speed);
  put(0x1084,F(F(cos(angle))*speed));put(0x1088,F(F(sin(angle))*speed));put(0x108c,0);
 }
}
