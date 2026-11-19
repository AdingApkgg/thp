const F=Math.fround;
// Original global fade object, 56 bytes. Requests: 76010/76050; tick: 75af0.
export class NativeFade {
 constructor(){this.state=new Uint8Array(56);this.v=new DataView(this.state.buffer);}
 get mode(){return this.v.getInt32(0x34,true);}
 get alpha(){return this.v.getInt32(0x28,true);}
 get color(){return this.v.getUint32(0x20,true);}
 requestIn(color,frames){this.request(color,frames,3);this.v.setInt32(0x2c,255,true);}
 requestOut(color,frames){this.request(color,frames,1);if(this.alpha>0)this.v.setInt32(8,Math.trunc((this.alpha*frames+254)/255),true);}
 request(color,frames,mode){this.v.setUint32(0x20,color&0xffffff,true);this.v.setInt32(0,frames,true);this.v.setInt32(8,0,true);this.v.setInt32(4,-999,true);this.v.setInt32(0x34,mode,true);}
 tick(){
  const v=this.v,mode=this.mode,frames=v.getInt32(0,true),clock=v.getInt32(8,true);
  if(mode===1){
   const alpha=frames===0?255:Math.trunc(F(F(F(clock)*F(255))/F(frames)));
   v.setInt32(0x28,Math.min(alpha,255),true);
   if(clock>=frames){v.setInt32(0x28,255,true);v.setInt32(0x34,2,true);return;}
  }else if(mode===3){
   const start=v.getInt32(0x2c,true);
   const alpha=frames===0?0:Math.trunc(F(F(start)-F(F(F(clock)*F(start))/F(frames))));
   v.setInt32(0x28,Math.max(0,alpha),true);
   if(clock>=frames){v.setInt32(0x34,0,true);v.setInt32(0x28,0,true);return;}
  }else{v.setInt32(0x28,mode===2?255:0,true);return;}
  v.setInt32(4,clock,true);v.setInt32(8,(clock+1)|0,true);
 }
}
