import {advanceTitleReturnTween} from './title-selection-return.mjs';
// Common owner processing for the implemented main/start/difficulty paths.
// Slide drawing, return tween and unrelated destination owners remain separate.
export function advanceTitleOwnerCommon(group,state,backdrop,{previousState=state.state,disabled=new Uint8Array(173),hasTexture=()=>true,backgroundEnabled=state.backgroundEnabled??true}={}){
 if(![0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31].includes(state.state)||![0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31].includes(previousState))throw Error('TH06nc: unsupported title owner common path');
 let next={...state};
 if(((previousState===next.state&&[3,4,6,7,9,11,13,14,18,20,22,24,28,29,30].includes(next.state))||(previousState===2&&next.state===3))&&!(next.entryHold&&next.state===3&&next.frame<36)){
  const t=(next.pulse+1)|0;next.pulse=t-Math.trunc(t/72)*72;
 }
 next.frame=(next.frame+1)|0;next.totalFrame=((next.totalFrame??0)+1)|0;
 if(next.inputCooldown>0)next.inputCooldown--;
 if(backdrop.counter>0){backdrop.counter--;if(backdrop.counter===0)backdrop.request(1);}
 if(next.entryHold&&(next.state!==3||next.frame>=36))next.entryHold=false;
 const options=[4,6,7].includes(next.state),previousOptions=[4,6,7].includes(next.previousGroupState);
 if(!(options&&!previousOptions&&next.state===4&&next.frame<=1)){if(options&&!previousOptions)group.slots.get(0x15990)?.interrupt(3);else if(!options&&previousOptions)group.slots.get(0x15990)?.interrupt(2);next.previousGroupState=next.state;}
 if(previousState===2&&next.state===3){group.slots.get(0x16170)?.interrupt(5);if(next.warmReturn){backdrop.request(6);next.warmReturn=false;}else{group.slots.get(0x16290)?.interrupt(2);backdrop.request(5);}}
 if(previousState===3&&next.state!==3){const id=next.state===4?3:4;group.slots.get(0x16290)?.interrupt(id);backdrop.request(id);}
 if(previousState===4&&next.state===3){group.slots.get(0x16170)?.interrupt(6);group.slots.get(0x16290)?.interrupt(2);backdrop.request(2);}
 const available=vm=>vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource);
 for(let i=0;i<173;i++){const vm=group.slots.get(0x9640+i*288);if(!disabled[i]&&available(vm))vm.tick();}
 next=advanceTitleReturnTween(group,next);
 const logo=group.slots.get(0x15990);if(available(logo))logo.tick();
 if(backgroundEnabled&&available(group.slots.get(0x16290)))backdrop.tick();
 return next;
}

