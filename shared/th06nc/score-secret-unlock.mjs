import {queueSound} from './sound-queue.mjs';
const letters='clasiger',sequence='classiclager';
export const scoreSecretCodes=[...letters].map(c=>'Key'+c.toUpperCase());

// Lunatic Score secret input, native 6e020/6e190. Raw controller bits are
// supplied by the input owner, independently from the menu navigation mask.
export function advanceScoreSecret({v},{keyboardMask=0,controllerMask=0,cleared,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const unlock=()=>{for(let profile=0;profile<4;profile++)cleared.fill(99,profile*24+12,profile*24+22);queueSound(soundSlots,28,{disabled:soundDisabled});};
 let success=false,fresh=(keyboardMask&~v.getInt32(0x4434,true))>>>0;v.setInt32(0x4434,keyboardMask,true);
 if(fresh){let progress=v.getInt32(0x4430,true);const bit=letters.indexOf(sequence[progress]);if(bit>=0&&(fresh&(1<<bit))){progress++;if(progress>=12){unlock();progress=0;success=true;}}else progress=Number(Boolean(fresh&1));v.setInt32(0x4430,progress,true);}
 fresh=(controllerMask&~v.getInt32(0x444c,true))>>>0;v.setInt32(0x444c,controllerMask,true);let progress=v.getInt32(0x4448,true);
 switch(progress){
  case 0:if((controllerMask&3)===3&&(fresh&3))progress=1;break;
  case 1:if(fresh&8)progress=2;else if(fresh&0x34)progress=0;break;
  case 2:if(fresh&4)progress=3;else if(fresh&0x38)progress=0;break;
  case 3:if((controllerMask&0x30)===0x30&&(fresh&0x30)){unlock();progress=0;success=true;}else if(fresh&0xc)progress=0;break;
  default:progress=0;
 }
 v.setInt32(0x4448,progress,true);if(success)v.setUint8(0x9e99,1);
}
