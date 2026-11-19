import {rebindAnm} from './anm-rebind.mjs';
const F=Math.fround;
// Remaining ECL enemy frame 28a7d..28d13. Firing/custom callbacks are host services.
export function finishEclEnemyFrame(enemy,nextOffset,{fireBullets=null,enemyCallback=null,anmBank=null,enemyAnms=null,operands=null}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);
 if(v.getInt32(0x234,true)>0){
  const interval=v.getInt32(0xf68,true);
  if(interval>0){
   const old=v.getInt32(0x10a4,true),clock=(old+1)|0;v.setInt32(0x10a0,old,true);v.setInt32(0x10a4,clock,true);
   if(clock>=interval){
    for(let i=0;i<3;i++)v.setFloat32(0x278+i*4,F(v.getFloat32(0xc5c+i*4,true)+v.getFloat32(0xb0+i*4,true)),true);
    if(!fireBullets)throw Error('TH06nc ECL: automatic shot requires the bullet service');fireBullets(enemy,enemy.subarray(0x26c,0x2d8));
    v.setInt32(0x10a4,0,true);v.setInt32(0x10a0,-999,true);
   }
  }
  if(v.getInt16(0xf6c,true)>=0){
   const vx=v.getFloat32(0x1084,true),direction=vx<0?1:vx>0?2:0,previous=v.getUint8(0xf7c);
   if(previous!==direction){
    const source=direction===1?0xf6c:direction===2?0xf6e:previous===255?0x109c:previous===1?0x2bc:0x2be;
    if(!anmBank||!enemyAnms)throw Error('TH06nc ECL: automatic animation requires the enemy ANM service');
    const vm=rebindAnm(anmBank,0x100+v.getInt16(source,true),enemy.subarray(0x108,0x228),{randomU16:operands?.environment.rng?()=>operands.environment.rng.next16():null});enemyAnms.set(0x108,vm);v.setUint8(0xf7c,direction);
   }
  }
  if(v.getBigUint64(0x98,true)!==0n){if(!enemyCallback)throw Error('TH06nc ECL: custom enemy callback not implemented');enemyCallback(enemy,0);}
 }
 v.setBigUint64(0x88,BigInt(nextOffset),true);const time=v.getInt32(0x44,true);v.setInt32(0x40,time,true);v.setInt32(0x44,(time+1)|0,true);
}
