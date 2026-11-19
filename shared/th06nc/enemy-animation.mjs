// World manager ANM phase 37875..379e0, after ECL and movement bounds.
export function advanceEnemyAnimations(entry){
 const {v,enemyAnms}=entry,main=enemyAnms.get(0x108);
 if(!main)throw Error('TH06nc: enemy main animation is not bound');
 main.v.setUint32(0xec,v.getUint32(0xf74,true),true);main.tick();v.setUint32(0xf74,main.v.getUint32(0xec,true),true);
 for(let i=0;i<8;i++){
  const offset=0x2d8+i*288;if(v.getInt16(offset+0x38,true)<0)continue;
  const vm=enemyAnms.get(offset);if(!vm)throw Error('TH06nc: enemy auxiliary animation metadata missing');if(vm.tick())vm.v.setInt16(0x38,-1,true);
 }
}
