const F=Math.fround;
export const defaultPlayfield=()=>new Float32Array([236,16,384,448]);
// Priority-14 owner 760f0 / initializer 76530 / update 76310.
export class ScreenShake {
 constructor({frames,amplitude,endAmplitude}){
  this.bytes=new Uint8Array(0x38);this.v=new DataView(this.bytes.buffer);this.v.setInt32(0,frames,true);this.v.setInt32(4,-999,true);this.v.setInt32(0x20,amplitude,true);this.v.setInt32(0x24,endAmplitude,true);this.v.setInt32(0x30,1,true);
 }
 tick(viewport,{rng,timeStop=false}={}){
  const {v}=this;if(timeStop){viewport.set([236,16,384,448]);return true;}
  const previous=v.getInt32(8,true),clock=(previous+1)|0,duration=v.getInt32(0,true);v.setInt32(4,previous,true);v.setInt32(8,clock,true);
  if(clock>=duration){viewport.set([236,16,384,448]);return false;}
  if(!rng)throw Error('TH06nc screen shake: RNG missing');
  const start=v.getInt32(0x20,true),end=v.getInt32(0x24,true),amplitude=F(F(F(F((end-start)|0)*F(clock))/F(duration))+F(start)),horizontal=rng.next32()%3,vertical=rng.next32()%3;
  viewport[0]=horizontal===1?F(F(236)+amplitude):236;viewport[2]=horizontal===0?384:F(F(384)-amplitude);viewport[1]=vertical===1?F(F(16)+amplitude):16;viewport[3]=vertical===0?448:F(F(448)-amplitude);return true;
 }
}
export class ScreenShakePool {
 constructor(environment={}){this.environment=environment;this.viewport=defaultPlayfield();this.effects=[];}
 spawn(request){const effect=new ScreenShake(request);this.effects.push(effect);return effect;}
 tick(){this.effects=this.effects.filter(effect=>effect.tick(this.viewport,this.environment));return this.effects.length;}
}
