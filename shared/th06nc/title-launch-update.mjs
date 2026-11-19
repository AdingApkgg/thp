const pulseColor=pulse=>{const t=pulse-Math.trunc(pulse/72)*72;const a=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);return ((a&255)<<24)|0xffffff;};
// Base final confirmation (state 24), before the fade/game handoff (state 25).
export function updateTitleLaunch(group,initial,keys,{hasTexture=()=>true,musicActive=false}={}){
 if(initial.state!==24||![14,22].includes(initial.launchFrom))throw Error('TH06nc: launch updater requires base final confirmation');
 const state={...initial},effects=[],at=p=>group.slots.get(p),vm=at(0x13a80);
 vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|9,true);vm.v.setUint32(0xec,pulseColor(state.pulse),true);
 for(const p of [0x18,0x1c,0x20])vm.v.setFloat32(p,0,true);
 if(state.frame<15)return {state,effects};
 const edge=bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit);
 if(edge(0x200)||edge(0x100))for(let tick=state.frame;tick<30;tick++)for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);if(vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();
 }
 if(edge(0x200)){
  state.state=state.launchFrom;state.frame=0;state.totalFrame=0;state.pulse=0;state.selection=Number(Boolean(state.configuredMode));
  for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(state.launchFrom===22?19:14);
  at(0x13960).interrupt(23);at(0x13a80).interrupt(23);at(0x9640+(130+state.difficulty)*288).interrupt(0);
  for(let c=0;c<2;c++)if(c!==state.configuredCharacter)for(const p of [0x122e0,0x12400,0x13060,0x13180])at(p+c*576).interrupt(0);
  at(0x13060+(state.configuredCharacter*2+state.configuredShot)*288).interrupt(20);if(state.launchFrom===22){state.selection=state.configuredPracticeStage;state.spell=1;at(0x13600+Number(Boolean(state.configuredMode))*288).interrupt(24);}effects.push({kind:'sound',id:11});
 }else if(edge(0x100)){
  effects.push({kind:'sound',id:10},{kind:'flushSoundQueue'},{kind:'fade',mode:0,frames:30});
  if(musicActive)effects.push({kind:'musicFade',frames:30});
  state.state=25;state.frame=0;
 }
 return {state,effects};
}
