import {bulletBytes,bulletCapacity,laserBytes,laserCapacity} from './projectile-cancel.mjs';
const F=Math.fround;
// EF00: full-power/spell-start clear. Conversion removes complete bullet slots;
// non-converting clear starts their cancel animation. Fading lasers spawn no items.
export function clearProjectiles({bullets,lasers,items=false,itemPool=null,sin=Math.sin,cos=Math.cos}={}){
 if(bullets?.byteLength!==bulletBytes*bulletCapacity||lasers?.byteLength!==laserBytes*laserCapacity)throw Error('TH06nc: projectile clear needs complete pools');
 if(items&&!itemPool)throw Error('TH06nc: projectile conversion needs item pool');
 const b=new DataView(bullets.buffer,bullets.byteOffset,bullets.byteLength),l=new DataView(lasers.buffer,lasers.byteOffset,lasers.byteLength);
 for(let slot=0;slot<bulletCapacity;slot++){
  const p=slot*bulletBytes,state=b.getUint16(p+0x44,true);if(!state||state===5)continue;
  if(items){itemPool.spawnPoint({position:Array.from({length:3},(_,k)=>b.getFloat32(p+0x30+k*4,true))});bullets.fill(0,p,p+bulletBytes);}else b.setUint16(p+0x44,5,true);
 }
 for(let slot=0;slot<laserCapacity;slot++){
  const p=slot*laserBytes;if(!l.getUint8(p+0x274))continue;
  if(l.getUint8(p+0x290)<2){
   l.setUint8(p+0x290,2);l.setInt32(p+0xc,0,true);l.setInt32(p+8,-999,true);
   if(items){const angle=l.getFloat32(p+0x260,true),s=F(sin(angle)),c=F(cos(angle)),head=l.getFloat32(p+0x14,true),x=l.getFloat32(p+0x278,true),y=l.getFloat32(p+0x27c,true);for(let t=l.getFloat32(p+0x10,true);head>t;t=F(t+F(32)))itemPool.spawnPoint({position:[F(F(c*t)+x),F(F(s*t)+y),0]});}
  }
  l.setInt32(p,0,true);
 }
}

// F300: scored clear at spell completion. Existing cancel-state bullets count;
// laser conversion includes one extra item at the beam origin.
export function clearProjectilesWithScore({bullets,lasers,items=false,itemPool=null,popups,environment={},bossState=null,sin=Math.sin,cos=Math.cos}={}){
 if(bullets?.byteLength!==bulletBytes*bulletCapacity||lasers?.byteLength!==laserBytes*laserCapacity)throw Error('TH06nc: scored clear needs complete pools');
 if(!popups||(items&&!itemPool))throw Error('TH06nc: scored clear needs popup/item managers');
 const b=new DataView(bullets.buffer,bullets.byteOffset,bullets.byteLength),l=new DataView(lasers.buffer,lasers.byteOffset,lasers.byteLength);let value=2000,total=0;
 for(let slot=0;slot<bulletCapacity;slot++){
  const p=slot*bulletBytes;if(!b.getUint16(p+0x44,true))continue;const position=Array.from({length:3},(_,k)=>b.getFloat32(p+0x30+k*4,true));
  if(items)itemPool.spawnPoint({position});popups.publish({position,value,color:value>=12800?0xffffff00:0xffffffff});total=(total+value)|0;b.setUint16(p+0x44,5,true);value=Math.min(value+10,12800);
 }
 for(let slot=0;slot<laserCapacity;slot++){
  const p=slot*laserBytes;if(!l.getUint8(p+0x274))continue;
  if(l.getUint8(p+0x290)<2){
   l.setUint8(p+0x290,2);l.setInt32(p+0xc,0,true);l.setInt32(p+8,-999,true);
   if(items){const position=Array.from({length:3},(_,k)=>l.getFloat32(p+0x278+k*4,true));itemPool.spawnPoint({position});const angle=l.getFloat32(p+0x260,true),s=F(sin(angle)),c=F(cos(angle)),head=l.getFloat32(p+0x14,true);for(let t=l.getFloat32(p+0x10,true);head>t;t=F(t+F(32)))itemPool.spawnPoint({position:[F(F(c*t)+position[0]),F(F(s*t)+position[1]),0]});}
  }
  l.setInt32(p,0,true);
 }
 environment.score=(BigInt(environment.score??0)+BigInt(total))&0xffffffffffffffffn;
 if(total&&bossState)bossState.bonusPopup={previous:-999,frame:0,active:true,position:[620,32,0],value:total};return total;
}
