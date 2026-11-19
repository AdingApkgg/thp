// Effect draw task 2b310..2b389. Camera/GPU setup belongs to the scene renderer.
export function drawEffects(pool,draw){
 let calls=0;
 for(let slot=0;slot<512;slot++){
  const effect=pool.entry(slot),{v,vm}=effect;if(!v.getUint8(0x14))continue;if(!vm)throw Error('TH06nc: active effect draw animation missing');
  for(let i=0;i<3;i++)vm.v.setUint32(0xc8+i*4,v.getUint32(0x174+i*4,true),true);
  draw(vm,{space:'world',part:'effect',slot});calls++;
 }
 return calls;
}
