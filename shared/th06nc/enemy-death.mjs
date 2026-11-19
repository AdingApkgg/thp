import {releaseEnemyEffects} from './enemy-linked-effects.mjs';
// Enemy death, original manager 37b86..37fd0. Effect/item and projectile managers
// supply their state-changing services.
export const enemyItemDropCycle=Object.freeze([0,0,1,0,1,0,0,1,1,1,0,0,0,1,1,0,1,0,1,0,1,0,1,0,1,0,0,1,1,1,0,2]);
export function finishOrdinaryEnemyDeath(entry,{environment={},critical=false,spawnEffect=null,dropItem=null,bossState=null,cancelBossProjectiles=null}={}){
 const {v,dispatch}=entry;
 if(v.getInt32(0x234,true)>0||!(v.getUint8(0xbd)&1))return false;
 const clearBoss=()=>{if(bossState)bossState.active=false;else if(v.getUint8(0xbd)&8)throw Error('TH06nc: boss death state missing');environment.suppressSpawn=false;};
 const position=()=>Array.from({length:3},(_,i)=>v.getFloat32(0xb0+i*4,true));
 const effect=(type,count)=>{if(!spawnEffect)throw Error('TH06nc: enemy death effect service missing');spawnEffect({type,position:position(),count,color:0xffffffff});};
 const item=type=>{if(!dropItem)throw Error('TH06nc: enemy item service missing');dropItem({type,position:position(),critical:Boolean(critical)});};
 v.setInt32(0xa0,-1,true);v.setInt32(0xc54,-1,true);
 const kind=v.getUint8(0xbd)>>>5;
 if(kind===3){
  v.setInt32(0x234,1,true);v.setUint8(0xbd,v.getUint8(0xbd)&15);
  clearBoss();
  for(let i=0;i<3;i++)effect(v.getUint8(0x38),1);
 }else if(kind<=2){
  if(kind<=1){
   environment.score=(BigInt(environment.score??0)+BigInt(v.getInt32(0xc50,true)))&0xffffffffffffffffn;
   if(kind===1)v.setUint8(0xbd,v.getUint8(0xbd)&254);else v.setUint8(0xbc,v.getUint8(0xbc)&127);
   if(v.getUint8(0xbd)&8){clearBoss();releaseEnemyEffects(entry);}
  }
  const type=v.getInt8(0x10a8);
  if(type>=0){effect(v.getUint8(0x39)+4,3);item(type);}
  else if(type===-1){
   const count=(environment.enemyDeathCount??0)&65535;
   if(count%3===0){
    effect(v.getUint8(0x39)+4,6);
    const index=(environment.itemDropIndex??0)&65535;
    if(index>=32)throw Error('TH06nc: invalid item drop cycle index');
    item(enemyItemDropCycle[index]);environment.itemDropIndex=index+1>=32?0:index+1;
   }
   environment.enemyDeathCount=(count+1)&65535;
  }
  if((v.getUint8(0xbd)&8)&&!(environment.spellCounter|0)){
   if(!cancelBossProjectiles)throw Error('TH06nc: boss death projectile service missing');const bonus=cancelBossProjectiles()|0;
   environment.score=(BigInt(environment.score??0)+BigInt(bonus))&0xffffffffffffffffn;
   if(bonus){if(!bossState)throw Error('TH06nc: boss death state missing');bossState.bonusPopup={previous:-999,frame:0,active:true,position:[620,32,0],value:bonus};}
   if(environment.spellPractice)environment.spellFinished=true;
  }
  v.setInt32(0x234,0,true);
 }
 const services=dispatch.services,slots=services.soundSlots,sound=2+((entry.slot??0)&1);
 if(!services.soundDisabled)for(let i=0;i<3;i++){if(slots[i]<0){slots[i]=sound;break;}if(slots[i]===sound)break;}
 effect(v.getUint8(0x38),1);effect(v.getUint8(0x39)+4,4);
 const sub=v.getInt32(0xbe0,true);
 if(sub>=0){
  const id=(sub<<16)>>16,target=dispatch.program.subroutines[id];if(!target)throw Error('TH06nc: invalid enemy death subroutine');
  v.setFloat32(0xa8,-0.5,true);v.setFloat32(0xac,0.5,true);v.setUint32(0xbdc,0,true);v.setUint32(0x1080,0,true);v.setInt32(0x240,0,true);
  dispatch.pointer(target.offset);v.setInt32(0x44,0,true);v.setInt32(0x40,-999,true);v.setInt16(0x80,id,true);v.setInt32(0xbe0,-1,true);
 }
 return true;
}
