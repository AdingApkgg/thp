// Native state-11 character branch, 0x14004b49c..0x14004b91d.
export function updateTitleCharacter(group,initial,keys,{extraUnlockedShots=[[false,false],[false,false]],hasTexture=()=>true}={}){
 if(initial.state!==11)throw Error('TH06nc: character updater requires owner state 11');
 const state={...initial},effects=[];
 if(state.frame<15)return {state,effects};
 const edge=bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit);
 const at=p=>{const vm=group.slots.get(p);if(!vm)throw Error('TH06nc: missing character VM');return vm;};
 const broadcast=id=>{for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(id);};
 const clearPair=character=>{at(0x122e0+character*576).interrupt(0);at(0x12400+character*576).interrupt(0);};
 if(edge(0x200)||edge(0x100))for(let tick=state.frame;tick<30;tick++)for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);if(vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();
 }
 if(edge(0x200)){
  const old=state.selection;state.state=9;state.frame=0;state.totalFrame=0;state.pulse=0;
  broadcast(state.difficulty<4?6:18);state.selection=state.difficulty<4?state.configuredDifficulty:0;
  if(old!==0)clearPair(0);if(old!==1)clearPair(1);effects.push({kind:'sound',id:11});
 }else if(edge(0x100)){
  state.configuredCharacter=state.selection&255;state.state=13;state.frame=0;state.totalFrame=0;state.pulse=0;
  const shot=state.configuredShot??0;
  state.selection=state.difficulty<4||extraUnlockedShots[state.configuredCharacter]?.[shot]?shot:1-shot;
  broadcast(13);at(0x9640+(130+state.difficulty)*288).interrupt(0);
  if(state.configuredCharacter!==0)clearPair(0);if(state.configuredCharacter!==1)clearPair(1);
  if(state.configuredCharacter!==0){at(0x13060).interrupt(0);at(0x13180).interrupt(0);}
  if(state.configuredCharacter!==1){at(0x132a0).interrupt(0);at(0x133c0).interrupt(0);}
  effects.push({kind:'sound',id:10});
 }else{
  let direction=0;
  if((keys.held&0x40)&&(edge(0x40)||keys.repeat!==0))direction=1;
  else if((keys.held&0x80)&&(edge(0x80)||keys.repeat!==0))direction=-1;
  if(direction){
   let selected=state.selection+direction;if(selected>=2)selected-=2;if(selected<0)selected+=2;
   if(state.difficulty===4&&!extraUnlockedShots[selected]?.some(Boolean))return {state,effects};
   state.selection=selected;effects.push({kind:'sound',id:12});
   for(let c=0;c<2;c++){
    const label=direction===1?(c===selected?9:12):(c===selected?10:11);
    at(0x122e0+c*576).interrupt(label);at(0x12400+c*576).interrupt(label);
   }
  }
 }
 return {state,effects};
}
