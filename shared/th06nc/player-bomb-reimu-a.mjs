import {initializeAnm} from './anm-initialize.mjs';
import {queueSound} from './sound-queue.mjs';
const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI);
// Original profile-0 update d1a0..d9b7; eight homing/exploding orb slots.
export function updateReimuABomb(player,{itemPool,publishBombName,finishBombName,screenEffect,spawnEffect,soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos}={}){
 const {v,bytes,anms,anmBank,environment={}}=player,clock=v.getInt32(0x7ac4,true),previous=v.getInt32(0x7ac0,true),i=p=>v.getInt32(p,true),f=p=>v.getFloat32(p,true),si=(p,x)=>v.setInt32(p,x,true),sf=(p,x)=>v.setFloat32(p,F(x),true);
 const effect=(type,count,color,position)=>{if(!spawnEffect)throw Error('TH06nc bomb: effect service missing');spawnEffect({type,count,color,position});};
 if(clock>=i(0x9f20)){if(!finishBombName)throw Error('TH06nc bomb: caption completion service missing');finishBombName();v.setUint8(0x9ec8,0);return;}
 if(clock!==previous&&clock===0){
  if(!itemPool||!publishBombName)throw Error('TH06nc bomb: Reimu A services missing');publishBombName({key:'EXE_REIMU_A_BOMB_NAME',resourceSlot:16});si(0x9f20,300);si(0x7858,360);si(0x7854,-999);bytes.fill(0,0x9ee0,0x9f00);
  for(let slot=0;slot<1024;slot++){const p=slot*0x160;if(itemPool.storage[p])itemPool.storage[p+12]=1;}
  effect(12,1,0xff4040ff,player.position);v.setUint32(0x77dc,v.getUint32(0x7730,true),true);v.setUint32(0x77e0,v.getUint32(0x7734,true),true);sf(0x77d4,256);sf(0x77d8,256);
 }
 if(((clock-60)>>>0)<=119&&clock%16===0){
  const orb=Math.trunc((clock-60)/16);
  if(orb!==0){
   if(!environment.rng)throw Error('TH06nc bomb: RNG missing');si(0x9ee0+orb*4,1);sf(0x9f00+orb*4,4);const p=0x7a00+orb*12;
   for(let axis=0;axis<3;axis++)v.setUint32(p+axis*4,v.getUint32(0x7730+axis*4,true),true);
   const angle=F(F(environment.rng.float01()*TAU)-PI);sf(p+0x60,F(F(cos(angle))*f(0x9f00+orb*4)));sf(p+0x64,F(F(sin(angle))*f(0x9f00+orb*4)));si(0x380+orb*4,0);
   for(let part=0;part<4;part++){const offset=0x7ac8+orb*0x480+part*288;anms.set(offset,initializeAnm(anmBank,0x4a5+part,bytes.subarray(offset,offset+288),{randomU16:()=>environment.rng.next16()}));}
   queueSound(soundSlots,13,{disabled:soundDisabled});
  }
 }
 v.setUint8(0x7898,3);
 for(let orb=0;orb<8;orb++){
  const stateOffset=0x9ee0+orb*4,state=i(stateOffset),p=0x7a00+orb*12;if(state===0)continue;
  if(clock!==previous){
   if(state===1){
    const valid=f(0x7740)>F(-100),target=valid?0x7740:0x7730,dx=F(f(target)-f(p)),dy=F(f(target+4)-f(p+4)),distance=F(Math.sqrt(F(F(dy*dy)+F(dx*dx)))),divisor=Math.max(F(1),F(distance/F(f(0x9f00+orb*4)*F(.125)))),vx=F(F(dx/divisor)+f(p+0x60)),vy=F(F(dy/divisor)+f(p+0x64)),length=F(Math.sqrt(F(F(vy*vy)+F(vx*vx))));
    let speed=Math.min(F(10),length);if(F(1)>speed)speed=F(1);sf(0x9f00+orb*4,speed);sf(p+0x60,F(F(speed*vx)/length));sf(p+0x64,F(F(vy*speed)/length));
    sf(0x180+orb*12,48);sf(0x184+orb*12,48);for(let axis=0;axis<3;axis++)v.setUint32(orb*12+axis*4,v.getUint32(p+axis*4,true),true);si(0x300+orb*4,8);
    const area=0x7754+orb*16;sf(area,48);sf(area+4,48);v.setUint32(area+8,v.getUint32(p,true),true);v.setUint32(area+12,v.getUint32(p+4,true),true);
    if(i(0x380+orb*4)>=100||clock>=i(0x9f20)-30){
     const position=[f(p),f(p+4),f(p+8)];effect(6,8,0xffffffff,position);effect(12,1,0xff4040ff,position);si(stateOffset,2);
     for(let part=0;part<4;part++)v.setUint16(0x7ac8+orb*0x480+part*288+0x8a,1,true);
     sf(0x180+orb*12,256);sf(0x184+orb*12,256);si(0x300+orb*4,200);sf(area,256);sf(area+4,256);queueSound(soundSlots,15,{disabled:soundDisabled});
     if(!screenEffect)throw Error('TH06nc bomb: screen effect service missing');screenEffect({frames:16,amplitude:8,endAmplitude:0});
    }
   }else{const next=(state+1)|0;si(stateOffset,next>=30?0:next);}
  }
  sf(p,F(f(p)+f(p+0x60)));sf(p+4,F(f(p+4)+f(p+0x64)));
  for(let part=0;part<4;part++){const vm=anms.get(0x7ac8+orb*0x480+part*288);if(!vm)throw Error('TH06nc bomb: missing Reimu A ANM');vm.tick();}
 }
 si(0x7ac0,clock);si(0x7ac4,(clock+1)|0);
}
export function drawReimuABomb(player,draw){
 const {v,anms}=player;
 for(let orb=0;orb<8;orb++)if(v.getInt32(0x9ee0+orb*4,true)!==0)for(let part=0;part<4;part++){
  const vm=anms.get(0x7ac8+orb*0x480+part*288),a=vm?.v;if(!a)throw Error('TH06nc bomb: missing Reimu A draw ANM');for(let k=0;k<3;k++)a.setFloat32(0xc8+k*4,F(v.getFloat32(0x7a00+orb*12+k*4,true)+a.getFloat32(0x18+k*4,true)),true);draw(vm,{snap:true,space:'screen',part:'bomb',slot:orb*4+part,orb,layer:part});
 }
}
