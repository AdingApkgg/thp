import {releaseEnemyEffects} from './enemy-linked-effects.mjs';
const F=Math.fround;
// Entry 6, original 33e60. These paired particles use the ordinary effect pool,
// including its exhausted-pool sentinel; they are not linked to the enemy.
export function advancePairedParticles(enemy,{environment,spawnEffect,linkedEffects,sin=Math.sin,cos=Math.cos}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);
 if(v.getUint8(0xbe)&8){releaseEnemyEffects({v,linkedEffects});return;}
 let rotation=F(v.getFloat32(0x228,true)+F(.01745329238474369));if(rotation>=F(.7853981852531433))rotation=F(rotation-F(1.5707963705062866));v.setFloat32(0x228,rotation,true);
 const time=v.getInt32(0x2d0,true),previous=v.getInt32(0x2cc,true);
 if(time!==previous&&(time>120||(time>60&&time%2===0)||(time>30&&time%4===0)||time%8===0)){
  if(!environment?.rng||!spawnEffect)throw Error('TH06nc ECL: paired-particle services missing');
  const group=Math.trunc((time%16)/2),n=(group+(group?environment.rng.next16()%(group&65535):0))|0,angle=F(rotation-F(F(F(n)*F(Math.PI))/F(40)));let radius=F(F(F(F(n)*F(160))*F(.0625))+F(32));if(radius<F(-.7853981852531433))radius=F(radius+F(1.5707963705062866));
  const x=F(F(cos(angle))*radius),y=F(F(sin(angle))*radius),position=Array.from({length:3},(_,i)=>v.getFloat32(0xb0+i*4,true)),vy=F(F(F(F(n)*F(8))/F(60))-F(.2666666805744171));
  for(const sign of [1,-1]){
   const effect=spawnEffect({type:19,position:[sign===1?F(position[0]+x):F(position[0]-x),F(position[1]+y),position[2]],count:1,color:0xff3030ff});if(!effect?.v)throw Error('TH06nc ECL: particle state handle missing');
   const ev=effect.v,vx=F(F(F(environment.rng.float01()*F(40))-F(20))/F(60));ev.setFloat32(0x188,vx,true);ev.setFloat32(0x18c,vy,true);ev.setUint32(0x190,0,true);ev.setFloat32(8,F(-vx*F(.008333333767950535)),true);ev.setFloat32(0xc,F(-vy*F(.008333333767950535)),true);ev.setUint32(0x10,0x80000000,true);
  }
 }
 v.setInt32(0x2cc,time,true);v.setInt32(0x2d0,(time+1)|0,true);
}
