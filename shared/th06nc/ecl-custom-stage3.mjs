const F=Math.fround,PI=F(Math.PI),TAU=F(2*Math.PI),STEP=F(2.5132741928100586);
export function createStageThreePatternState(){return {positions:new Uint8Array(28),angles:new Uint8Array(24)};}
function normalize(angle){let iterations=0;while(angle>PI){angle=F(angle-TAU);if(iterations++>16)break;}while(angle<-PI){angle=F(angle+TAU);if(iterations++>16)break;}return angle;}
// Entry 2, original 32cf0. Position snapshots and six polygon angles are
// process-shared state, not per-enemy locals. Five segments emit every six ticks.
export function advanceStageThreePattern(enemy,{environment,fireBullets,soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),clock=v.getInt32(0x50,true),limit=v.getInt32(0x54,true);
 if(clock>=limit){v.setBigUint64(0x98,0n,true);return;}
 if(!environment)throw Error('TH06nc ECL: stage-three shared environment missing');
 const shared=environment.stageThreePatternState??=createStageThreePatternState(),p=new DataView(shared.positions.buffer,shared.positions.byteOffset,28),a=new DataView(shared.angles.buffer,shared.angles.byteOffset,24);
 let px=p.getFloat32(16,true),py=p.getFloat32(20,true),angle=a.getFloat32(4,true);
 if(clock===0){
  if(!environment.rng)throw Error('TH06nc ECL: stage-three RNG missing');
  for(let i=0;i<3;i++){p.setUint32(i*4,v.getUint32(0xb0+i*4,true),true);p.setFloat32(16+i*4,F((environment.playerPosition??[0,0,0])[i]),true);}
  px=p.getFloat32(16,true);py=p.getFloat32(20,true);angle=F(F(environment.rng.float01()*TAU)-PI);a.setFloat32(0,angle,true);angle=normalize(F(angle+STEP));a.setFloat32(4,angle,true);
 }
 if(clock%30===0){for(let i=0;i<6;i++){a.setFloat32(i*4,angle,true);angle=normalize(F(angle+STEP));}}
 if(clock%6===0){
  if(!environment.rng||!fireBullets)throw Error('TH06nc ECL: stage-three shot services missing');
  const ratio=F(F(clock)/F(limit)),travel=F(ratio*F(.10000000149011612)),cx=F(F(F(px-p.getFloat32(0,true))*travel)+p.getFloat32(0,true)),cy=F(F(F(py-p.getFloat32(4,true))*travel)+p.getFloat32(4,true)),spread=F(ratio+F(.5)),decrement=F(spread*F(.5235987901687622));v.setFloat32(0x2a0,F(spread*F(1.0471975803375244)),true);
  for(let i=0;i<5;i++){
   const from=a.getFloat32(i*4,true),to=a.getFloat32((i+1)*4,true),radius=v.getFloat32(0x64,true),x=F(F(cos(from))*radius),y=F(F(sin(from))*radius),t=F(F(clock%30)/F(30));
   const nextX=F(F(cos(to))*radius),nextY=F(F(sin(to))*radius),interpolatedX=F(F(F(nextX-x)*t)+x),interpolatedY=F(F(F(nextY-y)*t)+y);
   v.setFloat32(0x278,F(interpolatedX+cx),true);v.setFloat32(0x27c,F(interpolatedY+cy),true);v.setUint32(0x280,0,true);
   const speed=v.getFloat32(0x270,true),step=v.getFloat32(0x274,true);v.setFloat32(0x270,F(F(environment.rng.float01()*step)+speed),true);fireBullets(enemy,enemy.subarray(0x26c,0x2d8));v.setFloat32(0x270,speed,true);v.setFloat32(0x2a0,F(v.getFloat32(0x2a0,true)-decrement),true);
  }
  if(!soundDisabled)for(let slot=0;slot<3;slot++){if(soundSlots[slot]<0){soundSlots[slot]=22;break;}if(soundSlots[slot]===22)break;}
 }
 v.setInt32(0x50,(clock+1)|0,true);
}
