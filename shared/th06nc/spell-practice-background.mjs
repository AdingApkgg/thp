import {findSpellPractice} from './spell-practice-table.mjs';
import {advanceStd} from './std-update.mjs';

// Background preparation 77550..77732. Select the original main/midboss time,
// advance the real STD task, release earlier wait markers and retain the last.
export function prepareSpellPracticeBackground(state,ecl,table,environment,{setFogColor=null,setFogRange=null}={}){
 let mainTime=0,midTime=-1,fallbackTime=-1;
 const timeline=ecl?.timelines[0]?.instructions??[];
 for(let i=0;i<Math.min(10000,timeline.length);i++){
  const ins=timeline[i];if(ins.time<0)break;
  if(ins.opcode===8){if(ins.arg0===0){mainTime=ins.time;break;}if(ins.arg0===2&&midTime<0)midTime=ins.time;}
  else if((ins.opcode&0xfff9)===0&&fallbackTime<0&&ins.args.length>=16&&new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength).getInt16(14,true)===-2)fallbackTime=ins.time;
 }
 const row=findSpellPractice(table,environment.spellPracticeIndex),midboss=Boolean(row?.midboss);
 let targetTime=midboss?(midTime>=0?midTime:fallbackTime>=0?fallbackTime:mainTime):mainTime,waits=0,frames=0,lastTime=0;
 if(!state?.v.getBigUint64(0xa8,true))return {midboss,targetTime,frames,remainingWaits:waits};
 for(const ins of state.program.instructions.slice(0,10000)){if(ins.time===-1)break;waits+=Number(ins.opcode===5);lastTime=ins.time;}
 if(!midboss&&waits===0&&lastTime>targetTime&&lastTime<=((targetTime+1800)|0))targetTime=(lastTime+1)|0;
 for(;frames<targetTime;frames++){
  const index=state.v.getInt32(0x24,true),ins=state.program.instructions[index];
  if(ins?.opcode===5){if(waits<=1)break;waits--;state.v.setUint8(0x68,1);}
  advanceStd(state,{paused:Boolean(environment.backgroundPaused),setFogColor,setFogRange});
 }
 return {midboss,targetTime,frames,remainingWaits:waits};
}
