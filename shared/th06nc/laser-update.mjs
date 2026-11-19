const F=Math.fround;
// Projectile manager's laser loop, 11610..11938. Collision is the player service.
export function advanceLaser(laser,{collision=null}={}){
 const {v,main}=laser;if(!v.getUint8(0x274))return 'inactive';
 const sprite=main?.boundSprite;if(!sprite)throw Error('TH06nc: active laser sprite binding missing');
 let head=F(v.getFloat32(0x14,true)+v.getFloat32(0x26c,true)),tail=v.getFloat32(0x10,true),maximum=v.getFloat32(0x288,true);
 v.setFloat32(0x14,head,true);if(F(head-tail)>maximum){tail=F(head-maximum);v.setFloat32(0x10,tail,true);}if(0>tail){tail=0;v.setFloat32(0x10,0,true);}
 const length=F(head-tail),width=v.getFloat32(4,true),angle=v.getFloat32(0x260,true),size=[length,F(width*F(0.5))],origin=Array.from({length:3},(_,i)=>v.getFloat32(0x278+i*4,true)),center=[F(F(F(length*F(0.5))+tail)+origin[0]),origin[1]];
 v.setFloat32(0x108,F(width/F(F(sprite.x+sprite.width)-sprite.x)),true);v.setFloat32(0x104,F(length/F(F(sprite.y+sprite.height)-sprite.y)),true);v.setFloat32(0xc4,F(F(Math.PI/2)-angle),true);
 let mode=v.getUint8(0x290),frame=v.getInt32(0xc,true);const delay=v.getInt32(0x270,true),fade=v.getInt32(0x18,true),alphaMode=Boolean(v.getUint16(0x264,true)&1);
 const alpha=()=>{const x=F(F(F(frame)*F(255))/F(delay));let n=Number.isFinite(x)&&x>=-2147483648&&x<2147483648?Math.trunc(x):-2147483648;n=Math.min(n,255);v.setUint32(0x10c,n<<24,true);};
 if(mode===0){
  if(alphaMode)alpha();else{const start=(delay-Math.min(delay,30))|0,logical=frame>start?F(F(F(frame)*width)/F(delay)):F(1.2);v.setFloat32(0x108,F(logical*F(1/32)),true);}
  if(frame>=delay){v.setInt32(0xc,0,true);v.setInt32(8,-999,true);v.setUint8(0x290,1);mode=1;frame=0;}
 }
 if(mode===1){
  if(!collision)throw Error('TH06nc: laser collision service missing');collision({center,size,origin,angle,graze:frame%12===0});
  if(frame>=v.getInt32(0x268,true)){
   v.setUint8(0x290,2);v.setInt32(0xc,0,true);v.setInt32(8,-999,true);mode=2;frame=0;
   if(fade===0){v.setUint8(0x274,0);return 'ended';}
  }
 }
 if(mode===2){
  if(alphaMode)alpha();else if(fade>0)v.setFloat32(0x108,F(F(width-F(F(F(frame)*width)/F(fade)))*F(1/32)),true);
  if(frame>=fade){v.setUint8(0x274,0);return 'ended';}
 }
 if(v.getFloat32(0x10,true)>=F(640))v.setUint8(0x274,0);
 v.setInt32(8,frame,true);v.setInt32(0xc,(frame+1)|0,true);main.tick();return v.getUint8(0x274)?'active':'culled';
}
