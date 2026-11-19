import {navigateTitle} from './title-navigation.mjs';
const pulseColor=pulse=>{const t=pulse-Math.trunc(pulse/72)*72;const a=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);return ((a&255)<<24)|0xffffff;};
export function updateTitleDifficulty(group,initial,keys,{sound={},configuredCharacter=0,extraUnlockedCharacters=[false,false],hasTexture=()=>true}={}){
 if(initial.state!==9)throw Error('TH06nc: difficulty updater requires owner state 9');
 const state={...initial},effects=[];let soundSlots=[...(sound.slots??[-1,-1,-1])];
 const vmAt=offset=>{const vm=group.slots.get(offset);if(!vm)throw Error(`TH06nc: missing selection VM ${offset}`);return vm;};
 const clearOffset=vm=>{for(const p of [0x18,0x1c,0x20])vm.v.setFloat32(p,0,true);};
 if(state.difficulty<4){
  const nav=navigateTitle(state.selection,4,keys,sound);state.selection=nav.selection;soundSlots=nav.soundSlots;if(nav.direction)state.totalFrame=0;
  for(let i=0;i<4;i++){const vm=vmAt(0x12880+i*288);vm.v.setUint32(0xec,i===state.selection?pulseColor(state.pulse):0x60ffffff,true);clearOffset(vm);if(i!==state.selection)vm.v.setUint16(0x84,0,true);}
  const extra=vmAt(0x12d00);extra.v.setUint32(0xc4,extra.v.getUint32(0xc4,true)&~2,true);
 }else{
  for(let i=0;i<4;i++){const vm=vmAt(0x12880+i*288);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)&~2,true);}
  const extra=vmAt(0x12d00);extra.v.setUint32(0xec,pulseColor(state.pulse),true);clearOffset(extra);
 }
 if(state.frame<15)return {state,effects,soundSlots};
 const edge=bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit);
 if(edge(0x200)||edge(0x100)){
  for(let tick=state.frame;tick<30;tick++)for(let i=0;i<173;i++){
   const vm=group.slots.get(0x9640+i*288);if(vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();
  }
 }
 const broadcast=id=>{for(const [offset,vm]of group.slots)if(offset>=0x9640&&offset<0x15900)vm.interrupt(id);};
 if(edge(0x200)){
  state.state=10;state.frame=0;broadcast(4);effects.push({kind:'sound',id:11},{kind:'fade',mode:0,frames:30});
  if(state.difficulty<4){state.configuredDifficulty=state.selection&255;state.selection=state.practice?2:0;}else state.selection=1;
 }else if(edge(0x100)){
  state.state=11;state.frame=0;state.pulse=0;
  if(state.difficulty<4){state.difficulty=state.selection;state.selection=configuredCharacter;}
  else{state.difficulty=4;state.selection=extraUnlockedCharacters[configuredCharacter]?configuredCharacter:1-configuredCharacter;}
  state.configuredDifficulty=state.difficulty&255;broadcast(7);
  const label=vmAt(0x9640+(130+state.difficulty)*288);label.v.setUint32(0xec,0xffffffff,true);label.interrupt(8);
  if(state.selection!==0){vmAt(0x122e0).interrupt(0);vmAt(0x12400).interrupt(0);}
  if(state.selection!==1){vmAt(0x12520).interrupt(0);vmAt(0x12640).interrupt(0);}
  effects.push({kind:'sound',id:10});
 }
 return {state,effects,soundSlots};
}
