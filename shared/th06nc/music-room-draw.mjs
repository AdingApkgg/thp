import {enqueueAsciiText} from './ascii-text.mjs';
const F=Math.fround;
function pulseAlpha(clock){const t=clock-Math.trunc(clock/72)*72;return t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);}
// Music Room draw 58630..58b4e, including original background layer order,
// retained label VMs and the native Latin-1 number/selection-marker queue.
export function drawMusicRoom(owner,draw,{ascii}={}){
 const v=owner.v,emit=(offset,path='flat')=>draw(owner.vm(offset),{snap:true,offset,path});
 for(const [i,path]of [[0,'flat'],[2,'rotated'],[4,'rotated'],[3,'flat']])emit(0x2448+i*288,path);
 emit(0x29e8);const start=v.getInt32(0x2b08,true),ticks=v.getInt32(0x2444,true);
 for(let index=start;index<start+10;index++){
  const threshold=(index-start)*3;if(ticks<=threshold)continue;let alpha=F(1);
  if(ticks<threshold+18){const t=F(F(1)-F(F(ticks-threshold)/F(18)));alpha=F(F(1)-F(F(t*t)*t));if(alpha<=0)continue;}
  const selected=v.getInt32(0,true)===index,playing=Boolean(v.getUint8(0x2425))&&v.getInt32(0x2408,true)===index;
  let color=playing?0xffffffff:selected?((pulseAlpha(v.getInt32(0x242c,true))<<24)|0xffffff)>>>0:0xe0808080;
  if(alpha<=0)color&=0xffffff;else if(alpha<1)color=((Math.trunc(F(F(F(color>>>24)*alpha)+F(.5)))<<24)|(color&0xffffff))>>>0;
  const offset=8+index*288,vm=owner.vm(offset),a=vm.v,x=F(F(85)-F(F(F(1)-alpha)*F(32))),y=F(F(F((index-start+1)*18)+F(95))-F(20));a.setUint32(0xec,color,true);a.setFloat32(0xc8,x,true);a.setFloat32(0xcc,y,true);a.setFloat32(0xd0,0,true);ascii.v.setUint32(0x52cc,color,true);emit(offset);
  const marker=[F(x+F(-55)),F(y+F(-2.5999999046325684)),0];
  if(selected)enqueueAsciiText(ascii,{text:String.fromCharCode(127),position:marker});
  const position=[F(F(marker[0]+F(15))+F(5.400000095367432)),F(marker[1]+F(1.2000000476837158)),0];
  enqueueAsciiText(ascii,{text:String(index+1).padStart(2,' ')+'.',position,scale:[F(.85),F(.85)]});
 }
 for(let i=0;i<16;i++)emit(0x2b10+i*288);ascii.v.setUint32(0x52cc,0xffffffff,true);emit(0x2568);
}
