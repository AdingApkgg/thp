import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround,TAU=F(2*Math.PI),HALF_PI=F(Math.PI/2);
// Custom entry 4, original 333e0. The shared flag gates tasks at their own
// priorities; changing it here must not retroactively freeze earlier tasks.
export function changeTimeStop(enemy,instruction,{environment,bulletPool,spawnEffect,sin=Math.sin,cos=Math.cos,atan2=Math.atan2}={}){
 const e=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),mode=a.getInt32(4,true);
 if(mode<2){
  if(!environment||!spawnEffect)throw Error('TH06nc ECL: time-stop services missing');
  spawnEffect({type:12,position:Array.from({length:3},(_,i)=>e.getFloat32(0xb0+i*4,true)),count:1,color:0xffffffff});environment.timeStop=mode&255;
 }else{
  if(!bulletPool||!environment?.rng)throw Error('TH06nc ECL: time-stop projectile services missing');
  const hard=environment.difficulty>1,player=environment.playerPosition??[0,0,0];let remaining=hard?52:14;
  for(let slot=0;slot<640&&remaining;slot++){
   const entry=bulletPool.entry(slot),v=entry.v,state=v.getUint16(0x44,true),spriteId=Number(v.getBigUint64(0x150,true))-1,sprite=bulletPool.anmBank.sprites.get(spriteId);
   if(state===0||state===5||!sprite||spriteLogicalSize(sprite.sprite)[0]<30||v.getUint16(0x3c,true)===5)continue;
   if((environment.rng.next16()&3)!==0)continue;
   let vm=entry.anms[0];if(!vm){vm=bulletPool.anmBank.createVm(v.getUint16(0x88,true),{allowMissing:true});vm.state=entry.bytes.subarray(0x50,0x170);vm.v=new DataView(vm.state.buffer,vm.state.byteOffset,288);vm.resolveSprite=id=>bulletPool.anmBank.sprites.get(id);entry.anms[0]=vm;}
   v.setUint16(0x3c,5,true);vm.bindSprite(v.getInt16(0x86,true)+5);
   const dx=F(v.getFloat32(0x30,true)-player[0]),dy=F(v.getFloat32(0x34,true)-player[1]),distance=F(Math.sqrt(F(F(dx*dx)+F(dy*dy))));let angle;
   if(distance>128){angle=F(environment.rng.float01()*(hard?TAU:F(2.356194496154785)));if(!hard)angle=F(angle+F(.7853981852531433));}
   else{const base=F((dx===0&&dy===0?HALF_PI:F(atan2(dy,dx)))+HALF_PI);angle=F(F(environment.rng.float01()*TAU)+base);}
   v.setFloat32(0x40,angle,true);v.setFloat32(8,F(F(cos(angle))*v.getFloat32(0x24,true)),true);v.setFloat32(0xc,F(F(sin(angle))*v.getFloat32(0x24,true)),true);remaining--;
  }
 }
 e.setInt32(0x50,0,true);
}

// Entry 5, original 33a30: nine rotating shot origins every ninth ECL tick.
// These ticks continue during time stop, independently of the owner timer.
export function fireTimeStopFan(enemy,{environment,fireBullets,soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),clock=v.getInt32(0x50,true),group=Math.trunc(clock/9);
 if(clock%9===0){
  if(!fireBullets)throw Error('TH06nc ECL: time-stop shot service missing');
  const player=environment.playerPosition??[0,0,0],position=Array.from({length:3},(_,i)=>v.getFloat32(0xb0+i*4,true)),delta=position.map((x,i)=>F(player[i]-x));
  const length=F(Math.sqrt(F(F(F(delta[1]*delta[1])+F(delta[0]*delta[0]))+F(delta[2]*delta[2])))),inverse=Math.abs(length)<=F(1e-6)?0:F(1/length),odd=group&1,t=F(F(.5)-F(F(F(group)*F(.5))/F(9)));
  let axis=delta.map(x=>F(F(inverse*x)*F(odd?-256:256))),center=delta.map((x,i)=>F(F(x*t)+axis[i]));axis=axis.map(x=>-x);
  const s=F(sin(F(.7853981852531433))),c=F(cos(F(.7853981852531433)));let x=F(F(axis[1]*s)+F(axis[0]*c)),y=F(F(axis[1]*c)-F(axis[0]*s));
  const step=F(.1745329350233078),rs=F(sin(-step)),rc=F(cos(-step)),descriptor=new Uint8Array(108),d=new DataView(descriptor.buffer);d.setInt16(0x18,environment.difficulty>1?3:1,true);d.setInt16(0x1a,1,true);d.setInt16(0x2c,8,true);d.setInt16(0x2e,3,true);d.setFloat32(0x38,F(.5235987901687622),true);let angle=F(-.7853981852531433);
  for(let i=0;i<9;i++){
   const nextX=F(F(rs*y)+F(rc*x)),nextY=F(F(rc*y)-F(rs*x));x=nextX;y=nextY;
   [x,y,axis[2]].forEach((n,k)=>d.setFloat32(0xc+k*4,F(F(n+position[k])+center[k]),true));d.setFloat32(4,2,true);if(odd&&environment.difficulty<=1)d.setFloat32(0x34,angle,true);fireBullets(enemy,descriptor);angle=F(angle+step);
  }
  if(!soundDisabled)for(let slot=0;slot<3;slot++){if(soundSlots[slot]<0){soundSlots[slot]=7;break;}if(soundSlots[slot]===7)break;}
 }
 v.setInt32(0x50,(clock+1)|0,true);
}
