const F=Math.fround;
// Option spread/focus transition 694f6..696f4, before fire-input handling.
export function advancePlayerOptions(state,{power=0}={}){
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength),si=(p,x)=>v.setInt32(p,x,true),sf=(p,x)=>v.setFloat32(p,F(x),true),focus=Boolean(v.getUint8(0x785c));let mode=v.getInt8(0x79f8),x=0,y=0;
 const setMode=n=>{mode=n;v.setUint8(0x79f8,n);};
 if((power&65535)<8)setMode(0);else if(mode===0)setMode(1);
 for(let iteration=0;iteration<4;iteration++){
  if(mode===0){si(0x404,0);si(0x400,-999);break;}
  if(mode===1){si(0x404,0);si(0x400,-999);x=24;if(!focus)break;setMode(2);}
  else if(mode===3){si(0x404,0);si(0x400,-999);x=8;y=-32;if(focus)break;setMode(4);}
  if(mode!==2&&mode!==4)break;
  const branch=mode,old=v.getInt32(0x404,true),frame=(old+1)|0;si(0x400,old);si(0x404,frame);const t=F(F(frame)*F(0.125)),squared=F(t*t);
  if(branch===2){y=F(F(F(F(1)-t)*F(32))-F(32));x=F(F(24)-F(squared*F(16)));if(frame>=8)setMode(3);if(focus)break;setMode(4);}
  else{y=F(F(t*F(32))-F(32));x=F(F(24)-F(F(F(1)-squared)*F(16)));if(frame>=8)setMode(1);if(!focus)break;setMode(2);}
  si(0x404,8-v.getInt32(0x404,true));si(0x400,-999);
 }
 sf(0x7880,F(v.getFloat32(0x7880,true)-x));sf(0x788c,F(x+v.getFloat32(0x788c,true)));sf(0x7884,F(y+v.getFloat32(0x7884,true)));sf(0x7890,F(y+v.getFloat32(0x7890,true)));
 return {x,y,mode};
}
