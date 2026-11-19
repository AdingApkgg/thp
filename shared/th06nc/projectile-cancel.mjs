export const bulletBytes=0x620,bulletCapacity=640,laserBytes=0x298,laserCapacity=64;
// Timeout helper 37039..3709f: no score or item publication.
export function cancelTimeoutProjectiles({bullets,lasers}={}){
 if(bullets?.byteLength!==bulletBytes*bulletCapacity||lasers?.byteLength!==laserBytes*laserCapacity)throw Error('TH06nc: complete projectile pools required for timeout cancellation');
 const b=new DataView(bullets.buffer,bullets.byteOffset,bullets.byteLength),l=new DataView(lasers.buffer,lasers.byteOffset,lasers.byteLength);
 for(let slot=0;slot<bulletCapacity;slot++){const p=slot*bulletBytes+0x44,state=b.getUint16(p,true);if(state&&state!==5)b.setUint16(p,5,true);}
 for(let slot=0;slot<laserCapacity;slot++){const p=slot*laserBytes;if(!l.getUint8(p+0x274))continue;if(l.getUint8(p+0x290)<2){l.setUint8(p+0x290,2);l.setInt32(p+0xc,0,true);l.setInt32(p+8,-999,true);}l.setInt32(p,0,true);}
}
// Boss-death conversion block 37daa..37e5f. Bullet slots start at manager +8;
// their position/state are +30/+44. Lasers use +274 active and +290 mode.
export function cancelBossProjectiles({bullets,lasers,publishScore=null}={}){
 if(bullets?.byteLength!==bulletBytes*bulletCapacity||lasers?.byteLength!==laserBytes*laserCapacity)throw Error('TH06nc: complete projectile pools required for boss cancellation');
 const b=new DataView(bullets.buffer,bullets.byteOffset,bullets.byteLength),l=new DataView(lasers.buffer,lasers.byteOffset,lasers.byteLength);let value=2000,total=0;
 for(let slot=0;slot<bulletCapacity;slot++){
  const p=slot*bulletBytes;if(!b.getUint16(p+0x44,true))continue;
  if(!publishScore)throw Error('TH06nc: projectile score display service missing');
  publishScore({position:Array.from({length:3},(_,i)=>b.getFloat32(p+0x30+i*4,true)),value,color:value>=12800?0xffffff00:0xffffffff});
  total=(total+value)|0;b.setUint16(p+0x44,5,true);value=Math.min(value+10,12800);
 }
 for(let slot=0;slot<laserCapacity;slot++){
  const p=slot*laserBytes;if(!l.getUint8(p+0x274))continue;
  if(l.getUint8(p+0x290)<2){l.setUint8(p+0x290,2);l.setInt32(p+0xc,0,true);l.setInt32(p+8,-999,true);}l.setInt32(p,0,true);
 }
 return total;
}
