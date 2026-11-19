import {advanceBombSensitiveBoss} from './ecl-custom-boss.mjs';
import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround;
// Entry 13, original 352e0. The clock advances even on skipped emissions;
// descriptor edits are temporary, while the enemy's angle/radius stay intact.
export function fireExtraOrbit(enemy,instruction,{fireBullets,sin=Math.sin,cos=Math.cos}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),clock=v.getInt32(0x54,true),count=a.getInt32(4,true);
 if(clock%6===0&&count>0){
  if(!fireBullets)throw Error('TH06nc ECL: Extra orbit shot service missing');
  const descriptor=new Uint8Array(108);descriptor.set(enemy.subarray(0x26c,0x2bc));const d=new DataView(descriptor.buffer),step=F(F(2*Math.PI)/F(count)),radius=v.getFloat32(0x64,true);let angle=v.getFloat32(0x60,true);
  for(let i=0;i<count;i++){d.setFloat32(0xc,F(F(F(cos(angle))*radius)+F(192)),true);d.setFloat32(0x10,F(F(F(sin(angle))*radius)+F(224)),true);d.setFloat32(0x34,F(angle+v.getFloat32(0x5c,true)),true);fireBullets(enemy,descriptor);angle=F(angle+step);}
 }
 v.setInt32(0x54,(clock+1)|0,true);
}

// Entry 14, original 35460. Active saved lasers count even if their visible
// interval is empty. The end distance is read again after each shot service.
export function fireAlongSavedLasers(enemy,{laserBindings,fireBullets,sin=Math.sin,cos=Math.cos}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);v.setInt32(0x54,0,true);
 for(let i=0;i<8;i++){
  const pointer=v.getBigUint64(0xf80+i*8,true);if(!pointer)continue;
  const laser=laserBindings?.get(pointer);if(!laser?.v)throw Error('TH06nc ECL: Extra saved laser missing');const l=laser.v;if(!l.getUint8(0x274))continue;
  const angle=l.getFloat32(0x260,true),s=F(sin(angle)),c=F(cos(angle));let distance=l.getFloat32(0x10,true);
  while(l.getFloat32(0x14,true)>distance){
   if(!fireBullets)throw Error('TH06nc ECL: Extra laser shot service missing');
   v.setFloat32(0x278,F(F(c*distance)+l.getFloat32(0x278,true)),true);v.setFloat32(0x27c,F(F(s*distance)+l.getFloat32(0x27c,true)),true);v.setUint32(0x280,0,true);fireBullets(enemy,enemy.subarray(0x26c,0x2d8));distance=F(distance+F(48));
  }
  v.setInt32(0x54,v.getInt32(0x54,true)+1,true);
 }
}

// Entry 15, original 355a0. Each large bullet activates nearby stopped small
// bullets. Earlier activations change speed, excluding them from later scans.
export function advanceExtraProximity(enemy,services={}){
 const {bulletPool,sin=Math.sin,cos=Math.cos,atan2=Math.atan2}=services;if(!bulletPool)throw Error('TH06nc ECL: Extra proximity bullet pool missing');
 const e=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),size=v=>{const p=Number(v.getBigUint64(0x150,true)),sprite=p?bulletPool.anmBank.sprites.get(p-1)?.sprite:null;return sprite?spriteLogicalSize(sprite)[0]:null;};let count=0;
 for(let outer=0;outer<640;outer++){
  const big=bulletPool.entry(outer).v,state=big.getUint16(0x44,true),height=size(big);if(state===0||state===5||height===null||height<30)continue;count++;
  const base=F(atan2(F(big.getFloat32(0x34,true)-e.getFloat32(0xb4,true)),F(big.getFloat32(0x30,true)-e.getFloat32(0xb0,true))));
  for(let inner=0;inner<640;inner++){
   const entry=bulletPool.entry(inner),v=entry.v,status=v.getUint16(0x44,true),smallHeight=size(v);if(status===0||status===5||smallHeight===null||smallHeight>=30||v.getFloat32(0x24,true)!==0)continue;
   const dx=F(v.getFloat32(0x30,true)-big.getFloat32(0x30,true)),dy=F(v.getFloat32(0x34,true)-big.getFloat32(0x34,true)),distance=F(Math.sqrt(F(F(dx*dx)+F(dy*dy))));if(!(distance<64))continue;
   v.setUint16(0x14,v.getUint16(0x14,true)|0x10,true);v.setFloat32(0x24,F(.01),true);v.setInt32(0x2c,0,true);v.setInt32(0x28,-999,true);v.setInt32(0x48,120,true);
   const direction=F(atan2(F(v.getFloat32(0x34,true)-e.getFloat32(0xb4,true)),F(v.getFloat32(0x30,true)-e.getFloat32(0xb0,true)))),angle=F(F(F(direction-base)*F(2.200000047683716))+base);v.setFloat32(0x40,angle,true);v.setFloat32(0x608,F(F(cos(angle))*F(.01)),true);v.setFloat32(0x60c,F(F(sin(angle))*F(.01)),true);
   let vm=entry.anms[0];if(!vm){vm=bulletPool.anmBank.createVm(v.getUint16(0x88,true),{allowMissing:true});vm.state=entry.bytes.subarray(0x50,0x170);vm.v=new DataView(vm.state.buffer,vm.state.byteOffset,288);vm.resolveSprite=id=>bulletPool.anmBank.sprites.get(id);entry.anms[0]=vm;}v.setInt16(0x3c,(v.getInt16(0x3c,true)+1)<<16>>16,true);vm.bindSprite(v.getInt16(0x86,true)+v.getInt16(0x3c,true));
  }
 }
 advanceBombSensitiveBoss(enemy,services);e.setInt32(0x54,count,true);
}

// Entry 16, original 35850. The signed owner timer disables life scaling at
// 7200; mode zero uses wrapped integer multiplication for its local counter.
export function configureExtraHealth(enemy,instruction,{environment}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),life=v.getInt32(4,true)<7200?v.getInt32(0x234,true):0,health=F(life);
 if(a.getInt32(4,true)===0){v.setFloat32(0x64,F(F(2)-F(health/F(6000))),true);v.setInt32(0x74,(40+Math.trunc(Math.imul(life,240)/6000))|0,true);}
 else{
  if(!environment?.rng)throw Error('TH06nc ECL: Extra health RNG missing');
  const spanX=F(F(320)-F(F(health*F(160))/F(6000))),baseX=F(F(192)-F(spanX*F(.5))),spanY=F(F(128)-F(F(health*F(64))/F(6000))),baseY=F(F(96)-F(spanY*F(.5)));
  v.setFloat32(0x60,F(baseX+F(environment.rng.float01()*spanX)),true);v.setFloat32(0x64,F(baseY+F(environment.rng.float01()*spanY)),true);
 }
}

// Entry 18, original 35a30. Integer products wrap before signed division.
export function configureExtraFinal(enemy){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),life=v.getInt32(4,true)<7200?v.getInt32(0x234,true):0;
 v.setFloat32(0x58,F(F(.006000000052154064)-F(F(F(life)*F(.0010000000474974513))/F(6000))),true);
 for(const [offset,base,multiplier,sign]of [[0x4c,22,25,1],[0x50,370,350,1],[0x54,400,250,-1]])v.setInt32(offset,(base+sign*Math.trunc(Math.imul(life,multiplier)/6000))|0,true);
}
