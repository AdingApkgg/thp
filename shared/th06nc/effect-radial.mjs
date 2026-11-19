const F=Math.fround;
// Callbacks 2ae30/2af80, effects 17/18. Their ANM owns lifetime; the callback
// keeps evaluating the unclamped shrinking radius and always returns 1.
export function advanceRadialEffect(effect,{rng=null,sin=Math.sin,cos=Math.cos,duration=60}={}){
 const {v,bytes}=effect;
 if(v.getInt32(0x28,true)===0&&v.getInt32(0x24,true)!==0){
  if(!rng)throw Error('TH06nc: radial effect needs shared RNG');
  if(bytes)bytes.copyWithin(0x30,0x174,0x180);else for(let k=0;k<3;k++)v.setUint32(0x30+k*4,v.getUint32(0x174+k*4,true),true);
  const angle=F(F(rng.float01()*F(2*Math.PI))-F(Math.PI));v.setFloat32(0x18,F(cos(angle)),true);v.setFloat32(0x1c,F(sin(angle)),true);v.setUint32(0x20,0,true);
 }
 const radius=F(F(256)-F(F(F(v.getInt32(0x28,true))*F(256))/F(duration)));
 for(let k=0;k<3;k++)v.setFloat32(0x174+k*4,F(F(radius*v.getFloat32(0x18+k*4,true))+v.getFloat32(0x30+k*4,true)),true);
 return 1;
}
