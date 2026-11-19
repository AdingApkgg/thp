import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround;
// Table entry 0, original 32970. Main VM binding changes before velocity
// changes; existing spawning/fading states are retained except inactive/5.
export function transformStageTwoBullets(enemy,instruction,{bulletPool,spawnEffect,environment=bulletPool?.environment,sin=Math.sin,cos=Math.cos}={}){
 if(!bulletPool||!spawnEffect)throw Error('TH06nc ECL: custom projectile services missing');
 const e=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),mode=a.getInt32(4,true);
 spawnEffect({type:12,position:Array.from({length:3},(_,k)=>e.getFloat32(0xb0+k*4,true)),count:1,color:0xffffffff});
 for(let slot=0;slot<640;slot++){const entry=bulletPool.entry(slot),v=entry.v,state=v.getUint16(0x44,true);if(state===0||state===5)continue;let vm=entry.anms[0];if(!vm){vm=bulletPool.anmBank.createVm(v.getUint16(0x88,true),{allowMissing:true});vm.state=entry.bytes.subarray(0x50,0x170);vm.v=new DataView(vm.state.buffer,vm.state.byteOffset,288);vm.resolveSprite=id=>bulletPool.anmBank.sprites.get(id);entry.anms[0]=vm;}v.setUint16(0x3c,15,true);vm.bindSprite(v.getInt16(0x86,true)+15);
  if(mode===0){v.setUint32(0x24,0,true);v.setBigUint64(8,0n,true);v.setUint32(0x10,0,true);}
  else if(mode===1){if(!environment?.rng)throw Error('TH06nc ECL: custom bullet RNG missing');v.setUint16(0x14,v.getUint16(0x14,true)|0x10,true);v.setInt32(0x48,220,true);v.setInt32(0x2c,0,true);v.setInt32(0x28,-999,true);const angle=F(F(environment.rng.float01()*F(2*Math.PI))-F(Math.PI));v.setFloat32(0x608,F(F(cos(angle))*F(.01)),true);v.setFloat32(0x60c,F(F(sin(angle))*F(.01)),true);}
 }
}
// Table entry 1, original 32b60: randomized origin, then ordinary shot service.
export function fireStageTwoRandomShot(enemy,instruction,{environment,fireBullets}={}){
 if(!environment?.rng||!fireBullets)throw Error('TH06nc ECL: custom random-shot services missing');const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength);let span=F(a.getInt32(4,true));
 for(let k=0;k<3;k++)v.setFloat32(0x278+k*4,F(v.getFloat32(0xc5c+k*4,true)+v.getFloat32(0xb0+k*4,true)),true);
 const half=F(span*F(.5)),randomX=F(environment.rng.float01()*span);span=F(span*F(.75));v.setFloat32(0x278,F(F(randomX+v.getFloat32(0xb0,true))-half),true);
 const randomY=F(environment.rng.float01()*span);span=F(span*F(.5));v.setFloat32(0x27c,F(F(randomY+v.getFloat32(0xb4,true))-span),true);fireBullets(enemy,enemy.subarray(0x26c,0x2d8));
}
// Entry 8, original 34950. Allocation may change later pool slots during this
// scan, so eligibility is read at each visit, not collected in advance.
export function fireFromLargeBullets(enemy,{bulletPool,environment=bulletPool?.environment,fireBullets}={}){
 if(!bulletPool||!environment?.rng||!fireBullets)throw Error('TH06nc ECL: large-bullet shot services missing');
 let count=0;
 for(let slot=0;slot<640;slot++){
  const v=bulletPool.entry(slot).v,state=v.getUint16(0x44,true),pointer=Number(v.getBigUint64(0x150,true)),sprite=pointer?bulletPool.anmBank.sprites.get(pointer-1)?.sprite:null;
  if(state===0||state===5||!sprite||spriteLogicalSize(sprite)[0]<30)continue;
  const descriptor=new Uint8Array(108),d=new DataView(descriptor.buffer);d.setUint16(0,8,true);for(let i=0;i<3;i++)d.setUint32(0xc+i*4,v.getUint32(0x30+i*4,true),true);d.setInt16(0x18,1,true);d.setInt16(0x1a,1,true);d.setInt16(0x2c,3,true);d.setInt16(0x2e,1,true);d.setInt32(0x30,1,true);d.setFloat32(0x34,F(F(environment.rng.float01()*F(2*Math.PI))-F(Math.PI)),true);fireBullets(enemy,descriptor);count++;
 }
 new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength).setInt32(0x54,count,true);
}
