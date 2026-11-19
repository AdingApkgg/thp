// CLRD secondary progress, title practice entry 558c0..55a2f.
export function practiceStageCount(cleared,{difficulty,configuredCharacter:character,configuredShot:shot}){
 const count=Math.min(cleared[(character*2+shot)*24+17+difficulty],6);
 return difficulty===0&&count===6?5:count;
}
export function enterPracticeStages(group,initial,{cleared}){
 const count=practiceStageCount(cleared,initial),previous=initial.configuredPracticeStage??0;
 const state={...initial,state:22,frame:0,pulse:0,spell:0,selection:previous>=count?0:previous},at=p=>group.slots.get(p);
 for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(19);
 at(0x9640+(130+state.difficulty)*288).interrupt(0);
 for(let c=0;c<2;c++)if(c!==state.configuredCharacter)for(const p of [0x122e0,0x12400,0x13060,0x13180])at(p+c*576).interrupt(0);
 at(0x13060+(state.configuredCharacter*2+state.configuredShot)*288).interrupt(20);
 at(0x13600+Number(Boolean(state.configuredMode))*288).interrupt(24);
 return state;
}
