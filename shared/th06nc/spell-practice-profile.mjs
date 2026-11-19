import {initializeAnm} from './anm-initialize.mjs';

// Original portrait/character-label refresh 4f150.
export function refreshSpellCharacter(group,state,character,direction=0){
 state.stageDirection=direction|0;state.stageTransition=direction?10:0;
 for(let c=0;c<2;c++){
  const portrait=group.slots.get(0x122e0+c*576),label=group.slots.get(0x12400+c*576);
  portrait.v.setUint32(0xc4,portrait.v.getUint32(0xc4,true)&~1,true);portrait.interrupt(0);
  label.interrupt(direction?10+Number((character&255)!==c):((character&255)===c?7:0));
 }
}

// Original shot and profile-preview refresh 4f1f0.
export function refreshSpellProfile(group,state,character,shot,direction=0){
 state.orderDirection=direction|0;state.orderTransition=state.difficultyTransition=direction?10:0;state.profileTransition=direction?24:0;
 const profile=(character&255)*2+(shot&255),previous=group.slots.get(0x1a5f8);
 const vm=initializeAnm(group.bank,0x7c8+profile,previous?.state??new Uint8Array(288));
 vm.v.setUint16(0x36,vm.v.getUint16(0x34,true),true);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|0x2009,true);vm.v.setUint32(0xec,0xffffffff,true);
 for(const p of [0xe4,0xe8])vm.v.setUint32(p,0x3f9c18fa,true);group.slots.set(0x1a5f8,vm);
 for(let i=0;i<4;i++){
  const shotVm=group.slots.get(0x13060+i*288),selected=i===profile;
  shotVm.v.setUint32(0xec,0xffffffff,true);shotVm.v.setUint32(0xc4,(shotVm.v.getUint32(0xc4,true)&~1)|Number(selected),true);shotVm.interrupt(selected?20:0);
 }
}
