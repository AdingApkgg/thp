import {navigateTitle} from './title-navigation.mjs';
const pulseColor=pulse=>{const t=pulse-Math.trunc(pulse/72)*72;const a=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);return ((a&255)<<24)|0xffffff;};
// Native state 13, 0x14004b922..0x14004bce8. State 14 is a separate owner.
export function updateTitleShot(group,initial,keys,{sound={},extraUnlockedShots=[[false,false],[false,false]],configuredMode=false,hasTexture=()=>true}={}){
 if(initial.state!==13)throw Error('TH06nc: shot updater requires owner state 13');
 const state={...initial},effects=[];
 const nav=navigateTitle(state.selection,2,keys,sound);state.selection=nav.selection;
 if(nav.direction)state.totalFrame=0;
 if(state.difficulty===4&&!extraUnlockedShots[state.configuredCharacter]?.[state.selection]){state.selection=1-state.selection;state.totalFrame=0;}
 const at=p=>{const vm=group.slots.get(p);if(!vm)throw Error('TH06nc: missing shot VM');return vm;};
 const flags=(vm,bits)=>vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|bits,true);
 flags(at(0x13180),8);flags(at(0x133c0),8);
 for(let shot=0;shot<2;shot++){
  const vm=at(0x13060+(state.configuredCharacter*2+shot)*288);flags(vm,9);
  for(const p of [0x18,0x1c,0x20])vm.v.setFloat32(p,0,true);
  vm.v.setUint32(0xec,state.selection===shot?pulseColor(state.pulse):0xa0d0d0d0,true);
 }
 const result=()=>({state,effects,soundSlots:nav.soundSlots});
 if(state.frame<15)return result();
 const edge=bit=>(keys.held&bit)!==0&&(keys.held&bit)!==(keys.previous&bit);
 const broadcast=id=>{for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(id);};
 if(edge(0x200)||edge(0x100))for(let tick=state.frame;tick<30;tick++)for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);if(vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();
 }
 if(edge(0x200)){
  state.configuredShot=state.selection&255;state.state=11;state.frame=0;state.pulse=0;state.selection=state.configuredCharacter;
  broadcast(7);at(0x9640+(130+state.difficulty)*288).interrupt(0);
  for(let c=0;c<2;c++){
   at(0x122e0+c*576).interrupt(c===state.configuredCharacter?21:0);at(0x12400+c*576).interrupt(c===state.configuredCharacter?21:0);
   if(c!==state.configuredCharacter){at(0x13060+c*576).interrupt(0);at(0x13180+c*576).interrupt(0);}
  }
  effects.push({kind:'sound',id:11});
 }else if(edge(0x100)){
  state.configuredShot=state.selection&255;state.state=14;state.frame=0;state.totalFrame=0;state.pulse=0;state.selection=Number(configuredMode);
  at(0x13060+(state.configuredCharacter*2+state.configuredShot)*288).v.setUint32(0xec,0xffffffff,true);
  broadcast(14);at(0x9640+(130+state.difficulty)*288).interrupt(0);
  for(let c=0;c<2;c++)if(c!==state.configuredCharacter){
   at(0x122e0+c*576).interrupt(0);at(0x12400+c*576).interrupt(0);at(0x13060+c*576).interrupt(0);at(0x13180+c*576).interrupt(0);
  }
  at(0x13060+(state.configuredCharacter*2+state.configuredShot)*288).interrupt(20);effects.push({kind:'sound',id:10});
 }
 return result();
}
