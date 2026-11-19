import {initializeAnm} from './anm-initialize.mjs';
import {queueSound} from './sound-queue.mjs';
import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI);
// Profile 3 update e7f0..ebd9. HUD caption and priority-14 screen effects are
// explicit services, not replacements for their original owners.
export function updateMarisaBBomb(player,{itemPool,publishBombName,finishBombName,screenEffect,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const {v,bytes,anms,anmBank,environment={}}=player,clock=v.getInt32(0x7ac4,true),previous=v.getInt32(0x7ac0,true),si=(p,x)=>v.setInt32(p,x,true),sf=(p,x)=>v.setFloat32(p,F(x),true);
 if(clock>=v.getInt32(0x9f20,true)){
  if(!finishBombName)throw Error('TH06nc bomb: caption completion service missing');finishBombName();v.setUint8(0x9ec8,0);sf(0x7714,1);sf(0x7710,1);return;
 }
 if(clock!==previous&&clock===0){
  if(!itemPool||!publishBombName)throw Error('TH06nc bomb: item/caption services missing');
  for(let slot=0;slot<1024;slot++){const p=slot*0x160;if(itemPool.storage[p])itemPool.storage[p+0xc]=1;}
  publishBombName({key:'EXE_MARISA_B_BOMB_NAME',resourceSlot:16});
  si(0x9f20,300);si(0x7858,360);si(0x7854,-999);
  for(let i=0;i<4;i++){
   const offset=0x7ac8+i*288;anms.set(offset,initializeAnm(anmBank,0x428+i,bytes.subarray(offset,offset+288),{randomU16:environment.rng?()=>environment.rng.next16():null}));
   for(let axis=0;axis<3;axis++)v.setUint32(0x7a00+i*12+axis*4,v.getUint32(0x7730+axis*4,true),true);
  }
  queueSound(soundSlots,19,{disabled:soundDisabled});sf(0x7714,.3);sf(0x7710,.3);
 }else{
  if(clock===60||clock===120){if(!screenEffect)throw Error('TH06nc bomb: screen effect service missing');screenEffect(clock===60?{frames:60,amplitude:1,endAmplitude:7}:{frames:200,amplitude:24,endAmplitude:0});}
  if(clock!==previous&&clock%4!==0){
   const y=v.getFloat32(0x7734,true),half=F(y*F(.5));sf(0x7758,y);sf(0x775c,192);sf(0x184,y);sf(0x7754,384);sf(0x7760,half);sf(4,half);sf(0x180,384);sf(0,192);si(0x300,12);
  }
  for(let i=0;i<4;i++){const vm=anms.get(0x7ac8+i*288);if(!vm)throw Error('TH06nc bomb: missing Marisa B ANM');vm.tick();}
 }
 si(0x7ac0,clock);si(0x7ac4,(clock+1)|0);v.setUint8(0x7898,3);
}
// ebe0..edd1: publish four screen-space VMs, then original 67f0 draw.
export function drawMarisaBBomb(player,draw,{sin=Math.sin,cos=Math.cos}={}){
 const {v,anms}=player;
 for(let i=0;i<4;i++){
  const vm=anms.get(0x7ac8+i*288),a=vm?.v;if(!a||!vm.boundSprite)throw Error('TH06nc bomb: missing Marisa B draw sprite');
  for(let axis=0;axis<3;axis++)a.setUint32(0xc8+axis*4,v.getUint32(0x7730+axis*4,true),true);
  const angle=F(F(F(F(F(i)*F(.6283185482025146))/F(3))-PI)+F(1.2566370964050293)),height=spriteLogicalSize(vm.boundSprite)[0],scale=a.getFloat32(0xe4,true);
  const delta=trig=>F(F(F(F(trig(angle))*height)*scale)*F(.5));a.setFloat32(0xc8,F(delta(cos)+a.getFloat32(0xc8,true)),true);a.setFloat32(0xcc,F(delta(sin)+a.getFloat32(0xcc,true)),true);
  let rotation=F(F(F(Math.PI/2)-angle)+PI),steps=0;
  while(rotation>PI){const before=steps++;rotation=F(rotation-TAU);if(before>16)break;}
  while(-PI>rotation){const before=steps++;rotation=F(rotation+TAU);if(before>16)break;}
  a.setFloat32(0xa4,rotation,true);a.setInt32(0xd0,0,true);draw(vm,{snap:true,space:'screen',part:'bomb',slot:i});
 }
}
