const F=Math.fround;
const integer=x=>!Number.isFinite(x)||x>=2147483648||x< -2147483648?-2147483648:Math.trunc(x);
// Original draw callback 2c600. Fade clocks advance here, per display call.
// Texture dimensions and the draw transports are caller-owned services.
export function drawEnding(bytes,{primary=-1,alternate=-1,useAlternate=false,viewport={x:0,y:0,width:854,height:480}}={},services={}){
 if(!(bytes instanceof Uint8Array)||bytes.length!==0x1280)throw Error('TH06nc ending draw: invalid owner');
 const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),get=p=>v.getInt32(p,true),put=(p,x)=>v.setInt32(p,x,true),handle=alternate!==-1&&useAlternate?alternate:primary;
 if(handle!==-1){const {width}=services.textureSize(handle);services.drawBackground({left:viewport.x|0,top:viewport.y|0,right:((viewport.x|0)+(viewport.width|0))|0,bottom:((viewport.y|0)+(viewport.height|0))|0,source:[integer(v.getFloat32(0x1240,true)),integer(v.getFloat32(0x1244,true)),width|0,width>1920?2160:1080],handle,transparent:0});}
 for(let i=0;i<16;i++){const offset=0x38+i*288;if(v.getUint16(offset+0x38,true)!==0)services.drawVm(offset,[255,255,1]);}
 const mode=get(0x30),clock=get(0),duration=get(4);
 if(mode===0)put(0x14,0);
 else if(mode===1||mode===3){
  if(clock>=duration){put(0x30,0);put(0x14,0);}
  else{const alpha=(-1-Math.trunc(Math.imul(clock,255)/duration))|0;put(0x14,(alpha<<24)|(mode===3?0xffffff:0));put(0,clock+1);}
 }else if(mode===2||mode===4){
  const alpha=clock>=duration?255:Math.trunc(Math.imul(clock,255)/duration);put(0x14,(alpha<<24)|(mode===4?0xffffff:0));if(clock<duration)put(0,clock+1);
 }
 const color=v.getUint32(0x14,true);if(color&0xff000000)services.drawFade({rect:[0,0,Math.max(F(viewport.width>>>0),854),Math.max(F(viewport.height>>>0),480)],color});
 return 1;
}
