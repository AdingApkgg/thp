import {integrateEnemyPosition} from './enemy-position.mjs';
import {tickEclEnemy} from './ecl-tick.mjs';
import {advanceEnemyAnimations} from './enemy-animation.mjs';
import {finishOrdinaryEnemyDeath} from './enemy-death.mjs';
import {advanceOrdinaryEnemyPhase} from './enemy-phase.mjs';
import {updateBossGauge} from './boss-state.mjs';
import {advanceEnemyEffects,releaseEnemyEffects} from './enemy-linked-effects.mjs';
import {spriteLogicalSize} from './sprite-layout.mjs';
const F=Math.fround;
// Enemy manager path; boss death/settlement remains explicit in the death helper.
export function tickOrdinaryEnemy(entry,{environment={},bodyCollision=null,damageQuery=null,spawnEffect=null,dropItem=null,cancelBullets=null,cancelTimeoutProjectiles=cancelBullets,bossState=null,cancelBossProjectiles=null}={}){
 const {v,enemy,enemyAnms,dispatch}=entry;
 if(!(v.getUint8(0xbc)&128))return 'inactive';
 const deactivate=reason=>{releaseEnemyEffects(entry);v.setUint8(0xbc,v.getUint8(0xbc)&127);if(v.getUint8(0xbd)>=32)v.setUint8(0xbd,v.getUint8(0xbd)&254);if(v.getUint8(0xbd)&8){if(!bossState)throw Error('TH06nc: boss state missing');bossState.active=false;environment.suppressSpawn=false;}return reason;};
 integrateEnemyPosition(enemy);
 const sprite=enemyAnms.get(0x108)?.boundSprite;if(!sprite)throw Error('TH06nc: active enemy requires a bound sprite');
 const size=spriteLogicalSize(sprite),x=v.getFloat32(0xb0,true),y=v.getFloat32(0xb4,true),halfX=F(F(size[1])*F(0.5)),halfY=F(F(size[0])*F(0.5));
 const outside=F(x+halfX)<0||F(x-halfX)>384||F(y+halfY)<0||F(y-halfY)>448;
 if(!(v.getUint8(0xbd)&4)&&!outside)v.setUint8(0xbd,v.getUint8(0xbd)|4);
 if((v.getUint8(0xbd)&4)&&outside)return deactivate('culled');
 advanceOrdinaryEnemyPhase(entry,{environment,cancelBullets,cancelTimeoutProjectiles,bossState});
 Object.assign(entry.operands.environment,environment);
 const result=tickEclEnemy(dispatch);if(result.deleted)return deactivate('deleted');if(result.debugStopped)throw Error('TH06nc: ordinary update stopped by script debugger');
 if(v.getUint8(0xbe)&1)for(let i=0;i<2;i++){
  const p=0xb0+i*4,value=v.getFloat32(p,true),low=v.getFloat32(0x28+i*4,true),high=v.getFloat32(0x30+i*4,true);if(low>value)v.setFloat32(p,low,true);else if(value>high)v.setFloat32(p,high,true);
 }
 advanceEnemyAnimations(entry);
 if((v.getUint8(0xbd)&4)&&!(v.getUint8(0xbe)&8)){
  const priorLife=v.getInt32(0x234,true);let critical=false;
  if((v.getUint8(0xbd)&3)===3){
   if(!bodyCollision)throw Error('TH06nc: enemy body collision service missing');
   const collisionBox=Array.from({length:3},(_,i)=>F(v.getFloat32(0x2c0+i*4,true)*F(2/3)));
   if(bodyCollision(entry,collisionBox)===1&&(v.getUint8(0xbd)&9)===1)v.setInt32(0x234,(v.getInt32(0x234,true)-10)|0,true);
  }
  if(v.getUint8(0xbd)&1){
   if(!damageQuery)throw Error('TH06nc: enemy damage service missing');const query=damageQuery(entry);critical=Boolean(query.critical);let damage=Math.min(query.damage|0,70);
   environment.score=(BigInt(environment.score??0)+BigInt(Math.trunc(damage/5)*10))&0xffffffffffffffffn;
   if(environment.damageMode??Boolean(environment.spellCounter)){if(!critical)damage=damage>7?Math.trunc(damage/7):damage===0?0:1;else if(environment.criticalDamageEnabled)damage=damage>3?Math.trunc(damage/3):damage===0?0:1;else damage=0;}
   if(v.getUint8(0xbd)&16)v.setInt32(0x234,(v.getInt32(0x234,true)-damage)|0,true);
   const target=environment.aimTarget??[0,-1000,0];if(v.getFloat32(0xb4,true)>F(target[1]))environment.aimTarget=Array.from({length:3},(_,i)=>v.getFloat32(0xb0+i*4,true));
  }
  finishOrdinaryEnemyDeath(entry,{environment,critical,spawnEffect,dropItem,bossState,cancelBossProjectiles});
  updateBossGauge(entry,{bossState,environment});
  let flash=v.getUint8(0xc4c);
  if(flash){v.setUint8(0xc4c,flash-1);v.setUint32(0x1cc,v.getUint32(0x1cc,true)&~8,true);}
  else if(priorLife>v.getInt32(0x234,true)){
   const services=dispatch.services,slots=services.soundSlots;
   if(!services.soundDisabled)for(let i=0;i<3;i++){if(slots[i]<0){slots[i]=20;break;}if(slots[i]===20)break;}
   v.setUint32(0x1cc,v.getUint32(0x1cc,true)|8,true);v.setUint8(0xc4c,4);
  }else v.setUint32(0x1cc,v.getUint32(0x1cc,true)&~8,true);
 }
 advanceEnemyEffects(entry);
 if(!environment.suppressEnemyTimer&&!environment.timeStop){const time=v.getInt32(4,true);v.setInt32(0,time,true);v.setInt32(4,(time+1)|0,true);}
 return 'active';
}
