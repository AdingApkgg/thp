const F=Math.fround;

// 4eaf0: draw a temporary VM; the menu's retained animation is untouched.
export function drawSpellHighlight(vm,draw,{x=0,y=0,color=0xffffffff,ticks=0,direction=0,noticeClock=0,hasTexture=true}={}){
 if(!vm.pointer(0x100)||vm.boundBinding?.active===false||!hasTexture)return;
 const sprite=vm.boundSprite;if(!sprite)throw Error('TH06nc: highlight sprite missing');
 let scale=F(1),opacity=F(1),bob=F(0),angle=F(0);
 if((noticeClock|0)>0){
  const r=(60-(noticeClock|0))|0;
  if(r<4){bob=F(-8.88888931274414);scale=F(1.25);opacity=F(.75);}
  else if(r<18){
   const t=F(F(r-3)/F(14)),tt=F(t*t);
   opacity=F(F(F(F(2)-t)*t)*F(.25)+F(.75));
   bob=F(F(F(1)-tt)*F(-8.88888931274414));
   scale=F(F(1.25)-F(F(F(F(3)-F(t+t))*tt)*F(.25)));
  }else{
   const q=F(F(r-17)/F(42)),g=Math.min(F(1),F(F(r-17)*F(.25))),remaining=F(F(1)-q);
   const sine=F(Math.sin(F(F(q*F(Math.PI))*F(4)))),factor=q<F(.25)?F(F(sine*F(.4000000059604645))+F(1)):F(1);
   angle=F(F(F(3)-F(g+g))*F(g*g));angle=F(angle*F(.1745329350233078));angle=F(angle*remaining);angle=F(angle*remaining);angle=F(angle*factor);angle=F(angle*sine);
  }
 }else if((ticks|0)>0){
  const t=F(F((25-(ticks|0))|0)/F(24)),remaining=F(F(1)-t);
  angle=F(F(Math.sin(F(F(t*F(Math.PI))*F(3))))*F(F(F(F(direction|0)*F(.13962633907794952))*remaining)*remaining));
 }
 const clone=Object.assign(Object.create(Object.getPrototypeOf(vm)),vm),state=vm.state.slice();clone.state=state;clone.v=new DataView(state.buffer,state.byteOffset,state.byteLength);
 const v=clone.v,sx=v.getFloat32(0xe8,true),sy=v.getFloat32(0xe4,true);
 const baseX=F(F(F(F(sx*F(.5))*F(480))/F(1080))*F(59)),baseY=F(F(F(F(sy*F(.5))*F(480))/F(1080))*F(-59));
 const X=F(baseX+F(x)),Y=F(F(baseY*F(scale-F(1)))+F(F(y)+bob)),newX=F(sx*scale),newY=F(sy*scale);
 const W=F(F(F(F(newX*F(sprite.width))*F(.4444444477558136))*F(.5))-F(baseX*scale)),H=F(F(F(newY*F(sprite.height))*F(.4444444477558136))*F(.5));
 const sine=F(Math.sin(angle)),cosine=F(Math.cos(angle));
 v.setFloat32(0xc8,F(F(X+F(W*cosine))+F(H*sine)),true);v.setFloat32(0xcc,F(F(Y-F(W*sine))+F(H*cosine)),true);
 v.setFloat32(0xa4,angle,true);v.setFloat32(0xe8,newX,true);v.setFloat32(0xe4,newY,true);v.setUint32(0xc4,v.getUint32(0xc4,true)&~0x700,true);
 color>>>=0;if(opacity<=0)color&=0xffffff;else if(opacity<1)color=((Math.trunc(F(F(F(color>>>24)*opacity)+F(.5)))<<24)|(color&0xffffff))>>>0;
 v.setUint32(0xec,color,true);draw(clone,{snap:false});
}
