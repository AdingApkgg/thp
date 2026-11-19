import {advancePairedParticles} from './ecl-custom-particles.mjs';
import {rebindAnm} from './anm-rebind.mjs';
// Entry 10, original 35050: paired particles plus bomb-sensitive boss state.
export function advanceBombSensitiveBoss(enemy,services={}, {restoreScript=0x1a0,restoreAutomatic=0xa1}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);if(v.getInt32(0x234,true)<=0)return;
 advancePairedParticles(enemy,services);
 const bomb=services.player?.v?Boolean(services.player.v.getUint8(0x9ec8)):Boolean(services.environment?.bombActive),bind=id=>{
  if(!services.anmBank||!services.enemyAnms)throw Error('TH06nc ECL: boss animation service missing');
  const vm=rebindAnm(services.anmBank,id,enemy.subarray(0x108,0x228),{randomU16:services.environment?.rng?()=>services.environment.rng.next16():null});services.enemyAnms.set(0x108,vm);
 };
 if(bomb){if(v.getInt16(0xf6c,true)>=0){bind(0x1a5);v.setInt16(0xf6c,-1,true);}v.setUint8(0xbd,v.getUint8(0xbd)&254);v.setInt32(0x1098,60,true);v.setInt32(0x1094,-999,true);}
 else{const clock=v.getInt32(0x1098,true);if(clock>0){v.setInt32(0x1098,clock-1,true);if(clock===1){if(v.getInt16(0xf6c,true)<0){bind(restoreScript);v.setInt16(0xf6c,restoreAutomatic,true);}v.setUint8(0xbd,v.getUint8(0xbd)|1);}}}
}
