const F=Math.fround;
// Enemy owner draw 38290..38667, with the 67f0 gameplay-offset bridge.
export function drawEnemyAnimations(entry,draw,{worldOffset=[0,0]}={}){
 const {v,enemyAnms}=entry;if(!(v.getUint8(0xbc)&128)||(v.getUint8(0xbe)&8))return;
 for(const offset of [0x2d8,0x3f8,0x518,0x638,0x108,0x758,0x878,0x998,0xab8]){
  if(offset!==0x108&&v.getInt16(offset+0x38,true)<0)continue;
  const vm=enemyAnms.get(offset);if(!vm)throw Error('TH06nc: missing enemy draw animation metadata');const a=vm.v;
  if((offset===0x108&&(v.getUint8(0xbe)&2))||(offset!==0x108&&a.getUint16(0x88,true)))a.setUint32(0xa4,v.getUint32(0x22c,true),true);
  for(let i=0;i<2;i++)a.setFloat32(0xc8+i*4,F(a.getFloat32(0x18+i*4,true)+v.getFloat32(0xb0+i*4,true)),true);
  a.setUint32(0xd0,offset===0x108?0x3efced91:0x3efd70a4,true);
  if((a.getUint32(0xc4,true)&3)!==3||a.getUint32(0xec,true)===0)continue;
  if(a.getFloat32(0x9c,true)!==0||a.getFloat32(0xa0,true)!==0){draw(vm,{space:'world'});continue;}
  const saved=vm.state.slice(0xc8,0xd4);
  try{
   for(let i=0;i<2;i++)a.setFloat32(0xc8+i*4,F(F(worldOffset[i])+a.getFloat32(0xc8+i*4,true)),true);
   draw(vm,{snap:a.getFloat32(0xa4,true)===0});
  }finally{vm.state.set(saved,0xc8);}
 }
}
