import {initializeAnm} from './anm-initialize.mjs';
import {queueSound} from './sound-queue.mjs';
const F=Math.fround;
// Original profile-1 update db50..e12b and four VM draws e130..e25f.
export function updateReimuBBomb(player,{itemPool,publishBombName,finishBombName,screenEffect,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const {v,bytes,anms,anmBank,environment={}}=player,clock=v.getInt32(0x7ac4,true),previous=v.getInt32(0x7ac0,true),si=(p,x)=>v.setInt32(p,x,true),sf=(p,x)=>v.setFloat32(p,F(x),true);
 if(clock>=v.getInt32(0x9f20,true)){if(!finishBombName)throw Error('TH06nc bomb: caption completion service missing');finishBombName();v.setUint8(0x9ec8,0);return;}
 if(clock!==previous&&clock===0){
  if(!itemPool||!publishBombName||!screenEffect)throw Error('TH06nc bomb: Reimu B services missing');
  for(let slot=0;slot<1024;slot++){const p=slot*0x160;if(itemPool.storage[p])itemPool.storage[p+12]=1;}
  publishBombName({key:'EXE_REIMU_B_BOMB_NAME',resourceSlot:17});si(0x9f20,140);si(0x7858,200);si(0x7854,-999);
  for(let i=0;i<4;i++){const offset=0x7ac8+i*288;anms.set(offset,initializeAnm(anmBank,0x4a9+i,bytes.subarray(offset,offset+288),{randomU16:environment.rng?()=>environment.rng.next16():null}));}
  queueSound(soundSlots,6,{disabled:soundDisabled});
  const x=v.getFloat32(0x7730,true),y=v.getFloat32(0x7734,true);[[x,224,.42],[192,y,.415],[x,224,.41],[192,y,.405]].forEach((p,i)=>p.forEach((x,k)=>sf(0x7a00+i*12+k*4,x)));
  screenEffect({frames:60,amplitude:2,endAmplitude:6});
 }else{
  if(clock===60){if(!screenEffect)throw Error('TH06nc bomb: screen effect service missing');screenEffect({frames:80,amplitude:20,endAmplitude:0});}
  for(let i=0;i<4;i++){sf(0x7754+i*16,i%2?384:62);sf(0x7758+i*16,i%2?62:448);}
  for(let i=0;i<4;i++){
   const offset=0x7ac8+i*288,vm=anms.get(offset);if(!vm)throw Error('TH06nc bomb: missing Reimu B ANM');vm.tick();
   if(clock!==previous&&(clock&1)){
    const position=Array.from({length:3},(_,k)=>F(v.getFloat32(0x7a00+i*12+k*4,true)+vm.v.getFloat32(0x18+k*4,true)));
    sf(0x775c+i*16,position[0]);sf(0x7760+i*16,position[1]);v.setUint32(0x180+i*12,v.getUint32(0x7754+i*16,true),true);v.setUint32(0x184+i*12,v.getUint32(0x7758+i*16,true),true);position.forEach((x,k)=>sf(i*12+k*4,x));si(0x300+i*4,8);
   }
  }
 }
 si(0x7ac0,clock);si(0x7ac4,(clock+1)|0);v.setUint8(0x7898,3);
}
export function drawReimuBBomb(player,draw){
 const {v,anms}=player;
 for(let i=0;i<4;i++){const vm=anms.get(0x7ac8+i*288),a=vm?.v;if(!a)throw Error('TH06nc bomb: missing Reimu B draw ANM');for(let k=0;k<2;k++)a.setFloat32(0xc8+k*4,F(v.getFloat32(0x7a00+i*12+k*4,true)+a.getFloat32(0x18+k*4,true)),true);a.setInt32(0xd0,0,true);draw(vm,{snap:true,space:'screen',part:'bomb',slot:i});}
}
