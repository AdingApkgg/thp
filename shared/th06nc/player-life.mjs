const F=Math.fround;
// Player state section 68ad2..69035. Main ANM publication, item manager and
// shared projectile pools are explicit services owned by the complete world.
export function advancePlayerLife(state,{environment={},resetMainAnimation=null,dropItem=null,cancelProjectiles=null}={}){
 const v=new DataView(state.buffer,state.byteOffset,state.byteLength),i=p=>v.getInt32(p,true),si=(p,x)=>v.setInt32(p,x,true),sf=(p,x)=>v.setFloat32(p,F(x),true),flags=(and,or)=>v.setUint32(0x798c,(v.getUint32(0x798c,true)&and)|or,true);
 const oldState=v.getUint8(0x7898);
 if(oldState===2){
  if(i(0x773c)!==0){
   si(0x773c,i(0x773c)-1);
   if(i(0x773c)===0){
    environment.deathCount=((environment.deathCount??0)+1)|0;environment.powerItemChain=0;
    if(!dropItem)throw Error('TH06nc: player death item service missing');const position=Array.from({length:3},(_,k)=>v.getFloat32(0x7730+k*4,true)),lives=(environment.lives??0)<<24>>24;
    if(lives>0){dropItem({type:2,position,critical:true});for(let k=0;k<5;k++)dropItem({type:0,position,critical:true});let power=environment.playerPower??0;power=power<=16?0:(power-16)&65535;if(environment.lifeProtection&&power<8)power=8;environment.playerPower=power;}
    else{for(let k=0;k<5;k++)dropItem({type:4,position,critical:true});environment.playerPower=0;environment.continueState=-1;}
    environment.inputFlags=((environment.inputFlags??0)&~16)|32;
   }
  }else{
   flags(-1,4);v.setBigUint64(0x789c,0n,true);const clock=i(0x7858),ratio=F(F(clock)/F(30));sf(0x79ac,F(F(ratio*F(3))+F(1)));sf(0x79b0,F(F(1)-ratio));const alpha=Math.trunc(F(F(255)-F(F(F(clock)*F(255))/F(30))));v.setUint32(0x79b4,(alpha<<24)|0xffffff,true);
   if(clock>=30){
    v.setUint8(0x7898,1);sf(0x7730,192);sf(0x7734,384);si(0x7858,0);si(0x7854,-999);sf(0x79ac,3);sf(0x79b0,3);sf(0x7738,0.2);
    if(!resetMainAnimation)throw Error('TH06nc: player respawn animation service missing');resetMainAnimation(0x420);
    const lives=(environment.lives??0)<<24>>24;
    if(lives<=0)environment.gameOverRequested=true;
    else{
     if(!environment.lifeProtection)environment.lives=(lives-1)&255;
     environment.inputFlags=(((environment.inputFlags??0)&~1)|2)&~4;
     environment.bombs=(environment.difficulty??0)<4&&!environment.practice?(environment.defaultBombs??3)&255:3;environment.inputFlags|=8;
     respawning();
    }
   }
  }
 }else if(oldState===1)respawning();
 if(i(0xa298)!==0){si(0xa298,i(0xa298)-1);if(!cancelProjectiles)throw Error('TH06nc: player respawn projectile service missing');cancelProjectiles();}
 if(v.getUint8(0x7898)===3){
  si(0x7858,i(0x7858)-1);const clock=i(0x7858);
  if(clock<=0){v.setUint8(0x7898,0);si(0x7858,0);si(0x7854,-999);flags(~8,0);v.setUint32(0x79b4,0xffffffff,true);}
  else if(clock%8<2){flags(-1,8);v.setUint32(0x79b4,0xff404040,true);}
  else{flags(~8,0);v.setUint32(0x79b4,0xffffffff,true);}
 }else{const clock=i(0x7858);si(0x7854,clock);si(0x7858,clock+1);}
 return v.getUint8(0x7898);
 function respawning(){
  const clock=i(0x7858);si(0xa298,90);flags(-1,4);sf(0x7710,1);sf(0x7714,1);si(0x773c,0);v.setUint32(0x79b4,(Math.trunc(Math.imul(clock,255)/30)<<24)|0xffffff,true);const ratio=F(F(clock)/F(30)),remainder=F(F(1)-ratio);sf(0x79ac,F(F(remainder+remainder)+F(1)));sf(0x79b0,F(F(1)-remainder));
  if(clock>=30){v.setUint8(0x7898,3);flags(~4,0);v.setUint32(0x79b4,0xffffffff,true);si(0x7858,240);si(0x7854,-999);sf(0x79ac,1);sf(0x79b0,1);si(0x773c,8);}
 }
}
