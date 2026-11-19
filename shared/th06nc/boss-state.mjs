// Boss registration opcode 101, native dispatch 271d3..27244.
export function createBossState(){return {active:false,lifeFraction:0,segmentFraction:0,dirty:false,remainingSeconds:0};}
export function setBossRegistration(enemy,index,{bossSlots,bossState,environment=null}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);
 if(index>=0){
  if(index>=8)throw Error('TH06nc: boss slot outside reserved table');
  bossSlots[index]={enemy,v};bossState.active=true;bossState.lifeFraction=1;bossState.segmentFraction=1;bossState.dirty=true;
  v.setUint8(0xbd,v.getUint8(0xbd)|8);v.setUint8(0x230,index&255);
 }else{
  bossState.active=false;bossSlots[v.getUint8(0x230)]=null;v.setUint8(0xbd,v.getUint8(0xbd)&247);bossState.dirty=true;
 }
 if(environment)environment.suppressSpawn=bossState.active;
}
// Manager health fractions, 37fd0..38077. Dialogs retain the previous fractions.
export function updateBossGauge(entry,{bossState,environment={}}){
 const {v}=entry;if(!(v.getUint8(0xbd)&8)||(environment.messageField36b0|0)>=0)return;
 if(!bossState)throw Error('TH06nc: boss gauge state missing');
 const F=Math.fround,life=v.getInt32(0x234,true),maximum=v.getInt32(0x238,true),phaseMaximum=v.getInt32(0x23c,true),threshold=Math.max(0,v.getInt32(0xa0,true));
 bossState.lifeFraction=maximum>0?F(F(life)/F(maximum)):0;
 if(phaseMaximum<=threshold)bossState.segmentFraction=life<=threshold?0:1;
 else bossState.segmentFraction=Math.max(0,Math.min(1,F(F((life-threshold)|0)/F((phaseMaximum-threshold)|0))));
}
