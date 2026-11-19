const F=Math.fround;
export function initializeEnemyLifeHud(state){return state.hudEnemyLife={smoothedFraction:0,opacity:0,segments:[0,0,0]};}
// Front ANM loop 3fd10..3ff48. Slot 19 has the enemy-life enter/exit
// state machine; dialogs advance its ordinary ANM instead of that machine.
export function advanceHudFront(state,bossState={active:false,lifeFraction:0}){
 const life=state.hudEnemyLife??initializeEnemyLifeHud(state),v=state.v;
 for(let i=0;i<33;i++){
  const offset=0xcc0+i*0x120;
  if(i!==19||v.getInt32(0x36b0,true)>=0){state.vm(offset).tick();continue;}
  let mode=v.getUint8(0x3ec0);
  if(bossState.active){
   if(mode===0){state.rebind(offset,0x633);v.setUint8(0x3ec0,1);life.opacity=0;}
   else{if(state.vm(offset).tick())v.setUint8(0x3ec0,2);life.opacity=(life.opacity>>>0)>=252?255:(life.opacity+4)|0;}
  }else if(mode!==0){
   if(mode<=2){state.rebind(offset,0x634);v.setUint8(0x3ec0,3);}
   life.opacity=life.opacity===0?0:(life.opacity-4)|0;
   if(state.vm(offset).tick()){v.setUint8(0x3ec0,0);life.smoothedFraction=0;life.segments.fill(0);life.opacity=0;}
  }
  if(v.getUint8(0x3ec0)>=2){
   const target=F(bossState.lifeFraction??0),current=F(life.smoothedFraction);
   if(target>current){const next=F(current+F(.01));life.smoothedFraction=next>target?target:next;}
   else if(current>target){const next=F(current-F(.02));life.smoothedFraction=target>next?target:next;}
  }
 }
 return life;
}
