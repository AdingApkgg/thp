import {enterPracticeStages} from './title-practice-entry.mjs';
import {navigateTitle} from './title-navigation.mjs';
const pulseColor=pulse=>{const t=pulse-Math.trunc(pulse/72)*72;const a=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);return ((a&255)<<24)|0xffffff;};
// Original selection handoff helper 0x14004da80. Resource/game creation follows later.
export function beginTitleLaunch(group,initial,{from=14,selectedMode=-1}={}){
 const state={...initial,state:24,frame:0,totalFrame:0,pulse:0,selection:0,launchFrom:from};
 const at=p=>group.slots.get(p);
 for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(-1);
 at(0x9640+(130+state.difficulty)*288).interrupt(0);
 at(0x122e0+state.configuredCharacter*576).interrupt(0);at(0x12400+state.configuredCharacter*576).interrupt(0);
 at(0x13060+(state.configuredCharacter*2+state.configuredShot)*288).interrupt(0);
 if(selectedMode>=0)at(0x13600+selectedMode*288).interrupt(24);
 for(const p of [0x13960,0x13a80]){
  const vm=at(p);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|9,true);vm.v.setUint32(0xec,0xffffffff,true);
  for(const o of [0x18,0x1c,0x20])vm.v.setFloat32(o,0,true);vm.interrupt(22);
 }
 return state;
}
export function updateTitleMode(group,initial,keys,{sound={},hasTexture=()=>true,cleared=null}={}){
 if(initial.state!==14)throw Error('TH06nc: mode updater requires base owner state 14');
 let state={...initial};const effects=[],nav=navigateTitle(state.selection,2,keys,sound);state.selection=nav.selection;
 if(nav.direction)state.totalFrame=0;
 const at=p=>group.slots.get(p);
 for(let i=0;i<2;i++){
  const vm=at(0x13600+i*288);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|9,true);
  vm.v.setUint32(0xec,state.selection===i?pulseColor(state.pulse):0xa0d0d0d0,true);
  for(const p of [0x18,0x1c,0x20])vm.v.setFloat32(p,0,true);
 }
 const hidden=at(0x13840);hidden.v.setUint32(0xc4,hidden.v.getUint32(0xc4,true)&~2,true);
 const result=()=>({state,effects,soundSlots:nav.soundSlots});
 if(state.frame<15)return result();
 const edge=bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit);
 if(edge(0x200)||edge(0x100))for(let tick=state.frame;tick<30;tick++)for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);if(vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();
 }
 if(edge(0x200)){
  state.configuredMode=state.selection;state.state=13;state.frame=0;state.totalFrame=0;state.pulse=0;state.selection=state.configuredShot;
  for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(13);
  at(0x9640+(130+state.difficulty)*288).interrupt(0);
  for(let c=0;c<2;c++)if(c!==state.configuredCharacter)for(const p of [0x122e0,0x12400,0x13060,0x13180])at(p+c*576).interrupt(0);
  effects.push({kind:'sound',id:11});
 }else if(edge(0x100)){
  effects.push({kind:'sound',id:10});state.configuredMode=state.selection;
  at(0x13600+state.selection*288).v.setUint32(0xec,0xffffffff,true);if(state.practice)state=enterPracticeStages(group,state,{cleared});else{state.stageIndex=state.difficulty<4?0:6;state=beginTitleLaunch(group,state,{from:14,selectedMode:state.selection});}
 }
 return result();
}
