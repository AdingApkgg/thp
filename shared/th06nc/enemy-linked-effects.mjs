const F=Math.fround;
const colors=Object.freeze([0xfff0f0f0,0xfff0f0f0,0xffffffff,0xffffe0e0,0xffffe0e0,0xffffe0e0,0xffffe0ff,0xffffe0ff,0xffffe0ff,0xffe0e0ff,0xffe0e0ff,0xffe0e0ff,0xffe0ffff,0xffe0ffff,0xffe0ffff,0xffe0ffe0,0xffe0ffe0,0xffe0ffe0,0xffe0ffe0,0xffe0ffe0,0xffe0ffe0,0xffffffe0,0xffffffe0,0xffffffe0,0xffffe0e0,0xffffe0e0,0xffffe0e0,0xffffffff]);
export function attachEnemyEffect(enemy,args,{spawnEffect,linkedEffects}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(args.buffer,args.byteOffset,args.byteLength),color=colors[a.getInt32(0,true)],index=v.getInt32(0x1090,true);
 if(color===undefined||index<0||index>=8)throw Error('TH06nc: invalid linked enemy effect parameters');
 if(!spawnEffect||!linkedEffects)throw Error('TH06nc: linked enemy effect service missing');
 const effect=spawnEffect({type:13,position:Array.from({length:3},(_,i)=>v.getFloat32(0xb0+i*4,true)),count:1,color});
 if(!effect?.v||!effect.pointer)throw Error('TH06nc: linked effect service must return a state handle');
 linkedEffects.set(effect.pointer,effect);v.setBigUint64(0xbe8+index*8,effect.pointer,true);
 for(let i=0;i<3;i++)effect.v.setUint32(0x18+i*4,a.getUint32(4+i*4,true),true);
 v.setUint32(0x268,a.getUint32(16,true),true);v.setInt32(0x1090,index+1,true);
}
function resolve(entry,pointer){const effect=entry.linkedEffects?.get(pointer);if(!effect)throw Error('TH06nc: linked effect handle missing');return effect;}
export function releaseEnemyEffects(entry){
 const {v}=entry,count=v.getInt32(0x1090,true);
 for(let i=0;i<count;i++){const p=0xbe8+i*8,pointer=v.getBigUint64(p,true);if(pointer){resolve(entry,pointer).v.setUint8(0x180,1);v.setBigUint64(p,0n,true);}}
 v.setInt32(0x1090,0,true);
}
export function advanceEnemyEffects(entry){
 const {v}=entry,count=v.getInt32(0x1090,true);
 for(let i=0;i<count;i++){
  const pointer=v.getBigUint64(0xbe8+i*8,true);if(!pointer)continue;const effect=resolve(entry,pointer).v;
  for(let k=0;k<3;k++)effect.setUint32(0x30+k*4,v.getUint32(0xb0+k*4,true),true);
  const strength=effect.getFloat32(0x184,true);if(v.getFloat32(0x268,true)>strength)effect.setFloat32(0x184,F(strength+F(0.3)),true);
  let angle=F(effect.getFloat32(0x2c,true)+F(Math.PI/100)),iterations=0;
  while(angle>F(Math.PI)){angle=F(angle+F(-2*Math.PI));if(iterations++>16)break;}
  while(F(-Math.PI)>angle){angle=F(angle+F(2*Math.PI));if(iterations++>16)break;}
  effect.setFloat32(0x2c,angle,true);
 }
}
