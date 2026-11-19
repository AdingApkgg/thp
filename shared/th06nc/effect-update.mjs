import {advanceOrbitEffect} from './effect-orbit.mjs';
import {advanceRadialEffect} from './effect-radial.mjs';
const F=Math.fround;
// Common drifting explosion callbacks 2a620/2a830 and integration 2aa50.
export function advanceEffectCallback(effect,{rng=null,sin=Math.sin,cos=Math.cos}={}){
 const {v}=effect,callback=Number(v.getBigUint64(0,true));if(callback===0)return 1;
 if(callback===0x14002aae0)return advanceOrbitEffect(effect,{sin,cos});
 if(callback===0x14002ae30||callback===0x14002af80)return advanceRadialEffect(effect,{rng,sin,cos,duration:callback===0x14002ae30?60:240});
 const burst=callback===0x14002a830,small=callback===0x14002a620,slow=callback===0x14002a410;
 if(!burst&&!small&&!slow&&callback!==0x14002aa50)throw Error(`TH06nc: effect callback ${callback.toString(16)} not implemented`);
 if((burst||small||slow)&&v.getInt32(0x28,true)===0&&v.getInt32(0x24,true)!==0){
  if(!rng)throw Error('TH06nc: effect callback needs shared RNG');
  for(let i=0;i<2;i++){
   let speed=F(F(rng.float01()*F(256))-F(128));speed=burst?F(F(speed*F(4))/F(33)):F(speed/F(slow?60:12));
   v.setFloat32(0x188+i*4,speed,true);v.setFloat32(8+i*4,F(F(-speed)*F(burst?0.05:slow?0.010526316240429878:0.05263157933950424)),true);
  }
  v.setUint32(0x190,0,true);v.setUint32(0x10,0x80000000,true);
 }
 for(let i=0;i<3;i++)v.setFloat32(0x174+i*4,F(v.getFloat32(0x174+i*4,true)+v.getFloat32(0x188+i*4,true)),true);
 for(let i=0;i<3;i++)v.setFloat32(0x188+i*4,F(v.getFloat32(0x188+i*4,true)+v.getFloat32(8+i*4,true)),true);
 return 1;
}
