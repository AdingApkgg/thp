// Native staggered Options entry and main-return delay, 4cbf4..4cd1a.
export function optionItemGroup(index){
 if(index<=20&&index>=0&&(0x1f4200&(1<<index)))return 0;
 if(index===10||(index>=21&&index<=24))return 1;
 if(index===11||(index>=25&&index<=34))return 2;
 if(index===12||(index>=35&&index<=44))return 3;
 if([13,45,46].includes(index))return 4;
 return ({49:5,109:6,108:7,15:8})[index]??-1;
}
export function advanceTitleOptionsEntry(group,initial,previousState){
 const state={...initial},interrupt=(matches,id)=>{for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900&&matches((p-0x9640)/288))vm.interrupt(id);};
 if(state.state===4&&previousState!==4){state.optionsEntry=true;interrupt(index=>optionItemGroup(index)>=0,0);interrupt(index=>optionItemGroup(index)===0,3);}
 else if(state.optionsEntry&&state.state===4&&state.frame>=1&&state.frame<9)interrupt(index=>optionItemGroup(index)===state.frame,3);
 if((state.inputDelay??0)>0){if(state.state===3&&previousState===3){state.inputDelay--;if(state.inputDelay===0)interrupt(index=>index>=51&&index<=69,2);}else if(state.state!==3)state.inputDelay=0;}
 return state;
}
