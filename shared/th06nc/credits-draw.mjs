import {enqueueAsciiText} from './ascii-text.mjs';
const F=Math.fround,mul=(a,b)=>F(F(a)*F(b)),add=(a,b)=>F(F(a)+F(b)),sub=(a,b)=>F(F(a)-F(b)),div=(a,b)=>F(F(a)/F(b)),cube=x=>mul(mul(x,x),x),smooth=x=>mul(sub(3,add(x,x)),mul(x,x));
function opacity(color,value){if(value<=0)return color&0xffffff;if(value>=1)return color>>>0;return ((Math.trunc(add(mul(color>>>24,value),.5))<<24)|(color&0xffffff))>>>0;}
function pulse(clock){const t=clock-Math.trunc(clock/72)*72;return t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);}
// Original13bf0: complete retained44-VM draw and ASCII footer animation.
export function drawCredits(state,draw,{ascii,drawBackground=()=>{}}={}){
 const {v}=state;drawBackground({color:0xffffffff});const slide=v.getInt32(0x20,true),direction=v.getInt32(0x24,true);let textScale=F(1),offset=F(0),oldAlpha=F(0),newAlpha=F(1);
 if(slide<5){let a=F(0),b=F(0);if(slide<=0){offset=mul(direction,4);textScale=F(.5);}else{textScale=slide>=3?F(1):add(mul(div(slide,3),.5),.5);b=div(slide,5);offset=mul(cube(sub(1,b)),mul(direction,4));a=slide<3?div(slide,3):F(1);}oldAlpha=sub(1,smooth(a));newAlpha=add(mul(smooth(b),.5),.5);}
 const reveal=v.getInt32(0x1c,true);
 for(let column=0;column<2;column++)for(let row=0;row<22;row++){
  const offset=0x48+(column*22+row)*288,vm=state.vm(offset),a=vm.v,oldX=a.getUint32(0xc8,true),color=a.getUint32(0xec,true),alpha=reveal<=row+3?F(0):reveal>=row+23?F(1):div(reveal-row-3,20);
  a.setFloat32(0xc8,add(a.getFloat32(0xc8,true),mul(cube(sub(1,alpha)),column===0?-8:8)),true);a.setUint32(0xec,opacity(color,mul(alpha,textScale)),true);try{draw(vm,{snap:true,offset,path:'flat'});}finally{a.setUint32(0xc8,oldX,true);a.setUint32(0xec,color,true);}
 }
 const enter=reveal<=24?F(0):reveal>=42?F(1):div(reveal-24,18),exitClock=v.getInt32(0x38,true),exit=exitClock<=0?F(0):exitClock>=15?F(1):div(exitClock,15),fade=mul(sub(1,exit),enter),left=direction<0?offset:F(0),right=direction>0?offset:F(0),y=add(mul(smooth(exit),3),add(mul(cube(sub(1,enter)),3),435));
 const total=v.getInt32(0x30,true),digits=String(total).length,label=page=>'  '+String(page+1).padStart(digits,' ')+(page+1<total?'-'+String(page+2).padStart(digits,' '):' '+''.padStart(digits,' '))+' / '+String(total).padStart(digits,' ')+'  ',current=label(v.getInt32(0x2c,true)),cell=mul(ascii.v.getFloat32(0,true),12),x=add(add(cell,cell),333),footerColor=opacity(((pulse(v.getInt32(0x18,true))<<24)|0xffffff)>>>0,fade),text=(value,position,color)=>{ascii.v.setUint32(0x52cc,color,true);enqueueAsciiText(ascii,{text:value,position});};
 text('<<',[add(left,333),y,0],footerColor);
 if(slide<5)text(label(v.getInt32(0x28,true)),[x,y,0],opacity(0xffffffff,mul(fade,oldAlpha)));
 text(current,[x,y,0],opacity(0xffffffff,mul(fade,newAlpha)));text('>>',[add(add(mul(current.length,cell),x),right),y,0],footerColor);ascii.v.setUint32(0x52cc,0xffffffff,true);
}
