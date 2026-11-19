import {navigateTitle} from './title-navigation.mjs';
import {practiceStageCount} from './title-practice-entry.mjs';
import {beginTitleLaunch} from './title-mode-update.mjs';
// Practice stage owner 22, 4bf63..4c193. Common clocks/ANMs follow later.
export function updatePracticeStages(group,initial,keys,{cleared,sound={},hasTexture=()=>true}={}){
 if(initial.state!==22)throw Error('TH06nc: practice stage owner required');
 const nav=navigateTitle(initial.selection,practiceStageCount(cleared,initial),keys,sound),effects=[];
 let state={...initial,selection:nav.selection};const at=p=>group.slots.get(p),result=()=>({state,effects,soundSlots:nav.soundSlots});
 if(state.frame<15)return result();
 const edge=bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit);
 if(edge(512)||edge(256))for(let tick=state.frame;tick<30;tick++)for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);if(vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();
 }
 if(edge(512)){
  Object.assign(state,{state:14,frame:0,totalFrame:0,pulse:0,selection:Number(Boolean(state.configuredMode))});
  for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(14);
  at(0x9640+(130+state.difficulty)*288).interrupt(0);
  for(let c=0;c<2;c++)if(c!==state.configuredCharacter)for(const p of [0x122e0,0x12400,0x13060,0x13180])at(p+c*576).interrupt(0);
  at(0x13060+(state.configuredCharacter*2+state.configuredShot)*288).interrupt(20);effects.push({kind:'sound',id:11});
 }else if(edge(256)){
  state.stageIndex=state.selection;state.configuredPracticeStage=state.selection;effects.push({kind:'sound',id:10});
  state=beginTitleLaunch(group,state,{from:22,selectedMode:Number(Boolean(state.configuredMode))});
 }
 return result();
}
