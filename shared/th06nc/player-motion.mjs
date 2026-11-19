const F=Math.fround;
// Position integration/clamping and combat query bounds, 69384..694f6.
export function integratePlayerMovement(state,{velocity,bounds=[0,0,384,448]}={}){
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength),f=p=>v.getFloat32(p,true),sf=(p,x)=>v.setFloat32(p,F(x),true),xVelocity=F(velocity[0]),yVelocity=F(velocity[1]);
 sf(0x789c,xVelocity);sf(0x78a0,yVelocity);
 let x=F(F(xVelocity*f(0x7710))+f(0x7730)),y=F(F(yVelocity*f(0x7714))+f(0x7734));
 sf(0x7730,x);sf(0x7734,y);
 const minX=F(bounds[0]),minY=F(bounds[1]),maxX=F(F(bounds[2])+minX),maxY=F(F(bounds[3])+minY);
 if(minX>x){x=minX;sf(0x7730,x);}else if(x>maxX){x=maxX;sf(0x7730,x);}
 if(minY>y){y=minY;sf(0x7734,y);}else if(y>maxY){y=maxY;sf(0x7734,y);}
 const position=[x,y,f(0x7738)];
 for(let k=0;k<3;k++){
  sf(0xa29c+k*4,F(position[k]-f(0x9f28+k*4)));sf(0xa2a8+k*4,F(f(0x9f28+k*4)+position[k]));
  for(const target of [0x7880,0x788c])v.setUint32(target+k*4,v.getUint32(0x7730+k*4,true),true);
 }
 return position;
}
