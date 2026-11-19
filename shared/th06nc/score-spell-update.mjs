import {queueSound} from './sound-queue.mjs';
import {interruptScoreAnimations} from './score-menu-update.mjs';
import {navigateScoreHorizontal} from './score-rank-update.mjs';

// Score spell records, native 70062..707cc; publication is delayed to tick20.
export function advanceScoreSpell(state,{held=0,previous=0,repeat=0,spellRecords,localization={},publishText,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const {v,bytes}=state;if(v.getInt32(0x9e94,true)!==8)throw Error('TH06nc score: spell page required');
 const page=v.getInt32(0x9e7c,true),clock=v.getInt32(0x4450,true),count=v.getInt32(0xa4,true);
 if(v.getInt32(0x18,true)!==page&&clock===20){
  v.setInt32(0x18,page,true);
  for(let row=page*10;row<(page+1)*10&&row<count;row++){
   const offset=0x2b70+(row%10)*288,vm=state.vm(offset),record=spellRecords.get(bytes[0x1c+row]),key=record?.attempts?record.key:'EXE_UNKNOWN_SPELLCARD_NAME';
   vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x300)|0x400,true);
   publishText(vm,{offset,text:localization[key]??key,colors:[0xffffff,0,0x10101,0x40202]});
  }
 }
 if(clock<30)return;
 if(navigateScoreHorizontal(state,Math.max(1,Math.trunc((count+9)/10)),{held,previous,repeat,soundSlots,soundDisabled})){v.setInt32(0x4450,0,true);interruptScoreAnimations(state,v.getInt32(0xa8,true)+3);}
 if((held&512)&&((held&512)!==(previous&512))){queueSound(soundSlots,11,{disabled:soundDisabled});v.setInt32(0x9e94,0,true);v.setBigUint64(0x4450,1n,true);interruptScoreAnimations(state,1);v.setInt32(0x9e84,v.getInt32(0x9e7c,true),true);v.setInt32(0x9e7c,v.getInt32(0xa8,true),true);}
}
