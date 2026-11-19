import {initializeAnm} from './anm-initialize.mjs';
import {queueSound} from './sound-queue.mjs';
const F=Math.fround,TAU=F(2*Math.PI);
// Original profile-2 update e270..e64d and screen-VM publication e650..e7ee.
export function updateMarisaABomb(player,{itemPool,publishBombName,finishBombName,screenEffect,soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos}={}){
 const {v,bytes,anms,anmBank,environment={}}=player,clock=v.getInt32(0x7ac4,true),previous=v.getInt32(0x7ac0,true),si=(p,x)=>v.setInt32(p,x,true),sf=(p,x)=>v.setFloat32(p,F(x),true);
 if(clock>=v.getInt32(0x9f20,true)){if(!finishBombName)throw Error('TH06nc bomb: caption completion service missing');finishBombName();v.setUint8(0x9ec8,0);return;}
 if(clock!==previous&&clock===0){
  if(!itemPool||!publishBombName||!screenEffect)throw Error('TH06nc bomb: Marisa A services missing');
  for(let slot=0;slot<1024;slot++){const p=slot*0x160;if(itemPool.storage[p])itemPool.storage[p+12]=1;}
  publishBombName({key:'EXE_MARISA_A_BOMB_NAME',resourceSlot:17});si(0x9f20,250);si(0x7858,310);si(0x7854,-999);
  for(let i=0;i<8;i++){
   const offset=0x7ac8+i*288;anms.set(offset,initializeAnm(anmBank,0x425+i%3,bytes.subarray(offset,offset+288),{randomU16:environment.rng?()=>environment.rng.next16():null}));
   for(let axis=0;axis<3;axis++)v.setUint32(0x7a00+i*12+axis*4,v.getUint32(0x7730+axis*4,true),true);
   const angle=F(F(F(i)*TAU)*F(.125)),x=F(cos(angle)),y=F(sin(angle));sf(0x7a60+i*12,F(x+x));sf(0x7a64+i*12,F(y+y));si(0x7a68+i*12,0);
  }
  queueSound(soundSlots,6,{disabled:soundDisabled});screenEffect({frames:120,amplitude:4,endAmplitude:1});
 }else{
  for(let i=0;i<8;i++){
   const p=0x7a00+i*12;for(let axis=0;axis<3;axis++)sf(p+axis*4,F(v.getFloat32(p+axis*4,true)+v.getFloat32(p+0x60+axis*4,true)));
   if(clock!==previous&&clock%3!==0){
    const area=0x7754+i*16;sf(area,128);sf(area+4,128);v.setUint32(area+8,v.getUint32(p,true),true);v.setUint32(area+12,v.getUint32(p+4,true),true);
    for(let axis=0;axis<3;axis++)v.setUint32(i*12+axis*4,v.getUint32(p+axis*4,true),true);sf(0x180+i*12,128);sf(0x184+i*12,128);si(0x300+i*4,8);
   }
   const vm=anms.get(0x7ac8+i*288);if(!vm)throw Error('TH06nc bomb: missing Marisa A ANM');vm.tick();
  }
 }
 si(0x7ac0,clock);si(0x7ac4,(clock+1)|0);v.setUint8(0x7898,3);
}
export function drawMarisaABomb(player,draw){
 const {v,anms}=player;
 for(let i=0;i<8;i++){
  const vm=anms.get(0x7ac8+i*288),a=vm?.v;if(!a)throw Error('TH06nc bomb: missing Marisa A draw ANM');
  const p=0x7a00+i*12,x=v.getFloat32(p,true),y=v.getFloat32(p+4,true),vx=v.getFloat32(p+0x60,true),vy=v.getFloat32(p+0x64,true);
  const publish=(x,y,scale,trail)=>{a.setFloat32(0xc8,x,true);a.setFloat32(0xcc,y,true);a.setInt32(0xd0,0,true);a.setFloat32(0xe8,F(scale),true);a.setFloat32(0xe4,F(scale),true);draw(vm,{snap:true,space:'screen',part:'bomb',slot:i,trail});};
  publish(x,y,3.2,0);
  const x1=F(F(x-F(vx*F(6)))-F(32)),y1=F(F(y-F(vy*F(6)))-F(32));publish(x1,y1,2.2,1);
  const dx=F(vx+vx),dy=F(vy+vy),x2=F(F(x1-dx)+F(64)),y2=F(F(y1-dy)+F(64));publish(F(F(x2-dx)-F(32)),F(F(y2-dy)-F(32)),1,2);
 }
}
