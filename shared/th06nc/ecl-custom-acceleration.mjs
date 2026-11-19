import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround;
// Entries 9/11, originals 34b50/34df0. Only stopped, small, live bullets
// receive acceleration; their existing velocity and displayed angle survive.
export function accelerateStoppedBullets(enemy,{bulletPool,environment=bulletPool?.environment,spawnEffect,sin=Math.sin,cos=Math.cos,randomEach=false}={}){
 if(!bulletPool||!environment?.rng||!spawnEffect)throw Error('TH06nc ECL: stopped-bullet services missing');
 const e=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),base=environment.rng.float01();let angle=F(F(base*F(2*Math.PI))-F(Math.PI));
 spawnEffect({type:12,position:Array.from({length:3},(_,i)=>e.getFloat32(0xb0+i*4,true)),count:1,color:0xffffffff});
 for(let slot=0;slot<640;slot++){
  const entry=bulletPool.entry(slot),v=entry.v,state=v.getUint16(0x44,true),pointer=Number(v.getBigUint64(0x150,true)),sprite=pointer?bulletPool.anmBank.sprites.get(pointer-1)?.sprite:null;
  if(state===0||state===5||!sprite||spriteLogicalSize(sprite)[0]>=30||v.getFloat32(0x24,true)!==0)continue;
  let vm=entry.anms[0];if(!vm){vm=bulletPool.anmBank.createVm(v.getUint16(0x88,true),{allowMissing:true});vm.state=entry.bytes.subarray(0x50,0x170);vm.v=new DataView(vm.state.buffer,vm.state.byteOffset,288);vm.resolveSprite=id=>bulletPool.anmBank.sprites.get(id);entry.anms[0]=vm;}
  v.setUint16(0x14,v.getUint16(0x14,true)|0x10,true);v.setUint16(0x3c,2,true);vm.bindSprite(v.getInt16(0x86,true)+2);v.setFloat32(0x24,F(.01),true);v.setInt32(0x2c,0,true);v.setInt32(0x28,-999,true);v.setInt32(0x48,120,true);
  if(randomEach)angle=F(F(environment.rng.float01()*F(2*Math.PI))-F(Math.PI));
  else{const dx=F(e.getFloat32(0xb0,true)-v.getFloat32(0x30,true)),dy=F(e.getFloat32(0xb4,true)-v.getFloat32(0x34,true)),squared=F(F(dx*dx)+F(dy*dy)),distance=squared>F(.1)?F(Math.sqrt(squared)):0;angle=F(F(F(distance*F(Math.PI))*F(.00390625))+F(F(base*F(2*Math.PI))-F(Math.PI)));}
  v.setFloat32(0x608,F(F(cos(angle))*F(.01)),true);v.setFloat32(0x60c,F(F(sin(angle))*F(.01)),true);
 }
}
