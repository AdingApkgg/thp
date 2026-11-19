import {queueSound} from './sound-queue.mjs';
import {resultProfileName} from './result-name-scene.mjs';
import {interruptScoreAnimations} from './score-menu-update.mjs';

// Native horizontal helper 6dc30, shared by rank and spell-record pages.
export function navigateScoreHorizontal({v},count,{held=0,previous=0,repeat=0,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const pressed=bit=>Boolean(held&bit)&&((held&bit)!==(previous&bit)||repeat!==0);let selected=v.getInt32(0x9e7c,true);
 if(pressed(64)){selected=(selected-1)|0;if(selected<0)selected+=count;}
 else if(pressed(128)){selected=(selected+1)|0;if(selected>=count)selected-=count;}
 else return false;
 v.setInt32(0x9e7c,selected,true);queueSound(soundSlots,12,{disabled:soundDisabled});return true;
}

// Rank pages3..7, 6fac3..7005d. Lunatic6 has an additional secret-unlock
// producer before this shared page body; supplied explicitly by its owner.
export function advanceScoreRank(state,{held=0,previous=0,repeat=0,localization={},publishText,soundSlots=[-1,-1,-1],soundDisabled=false,processSecretUnlock=null}={}){
 const {v}=state,kind=v.getInt32(0x9e94,true);if(kind<3||kind>7)throw Error('TH06nc score: rank page required');
 if(kind===6)processSecretUnlock?.(state,{held,previous,repeat});
 const selected=v.getInt32(0x9e7c,true),clock=v.getInt32(0x4450,true);
 if(v.getInt32(4,true)!==selected&&clock===20){
  v.setInt32(4,selected,true);const character=selected%2,mode=Math.trunc(selected/2);
  for(let side=0;side<2;side++){const offset=0x2b70+side*288,vm=state.vm(offset);vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x400)|0x300,true);vm.v.setUint32(0xec,0xffffffff,true);publishText(vm,{offset,text:resultProfileName(character*2+side,mode,localization),colors:[0xffffff,0,0x10101,0x40202]});}
 }
 if(clock<30)return;
 if(navigateScoreHorizontal(state,4,{held,previous,repeat,soundSlots,soundDisabled})){v.setInt32(0x4450,0,true);interruptScoreAnimations(state,v.getInt32(0xa8,true)+3);}
 if((held&512)&&((held&512)!==(previous&512))){
  queueSound(soundSlots,11,{disabled:soundDisabled});v.setInt32(0x9e94,0,true);v.setBigUint64(0x4450,1n,true);interruptScoreAnimations(state,1);v.setInt32(0x9e80,v.getInt32(0x9e7c,true),true);v.setInt32(0x9e7c,v.getInt32(0xa8,true),true);
 }
}
